"""StateClient on an append-only SQLite log (backend="sqlite").

Same API as the Chroma StateClient. Differences:
- add() only writes a row. Embeddings are computed later, in batches, when query() needs them,
  so add() is fast, works offline, and a failed embedding call never loses a state.
- get() reads by index (timestamp, then insertion order), so it does not slow down as states pile up.
- Each row also keeps seq (insertion order) and the module that wrote it.
  get(since_seq=n) returns only rows added after seq n.
- metadata filters support equality only ({"key": value, ...}).
- Rows not embedded yet have vector None in get().

One file per agent: <data_dir>/<agent_name>.sqlite (default data_dir: ./cma_state).
"""
import datetime, json, os, pickle, sqlite3, threading, uuid, warnings
import numpy as np
import chromadb
from .client import StateClient, _make_embedding_function
from .state import State

DEFAULT_DATA_DIR = "./cma_state"
EMBED_BATCH = 64

_SCHEMA = """
CREATE TABLE IF NOT EXISTS states (
    seq      INTEGER PRIMARY KEY AUTOINCREMENT,
    id       TEXT NOT NULL UNIQUE,
    ts       REAL NOT NULL,
    module   TEXT,
    text     TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    vector   BLOB
);
CREATE INDEX IF NOT EXISTS states_ts ON states (ts, seq);
"""

# Vectors are cached per database file and shared by every client in the process
# (each module thread has its own client; one copy of the vectors is enough).
_vector_caches = {}
_vector_caches_lock = threading.Lock()


class _VectorCache:
    def __init__(self):
        self.lock = threading.Lock()
        self.seqs = np.zeros(0, dtype=np.int64)
        self.vectors = None  # float32 (n, dim)
        self.max_seq = 0
        self.generation = None

    def reset(self):
        self.seqs = np.zeros(0, dtype=np.int64)
        self.vectors = None
        self.max_seq = 0


def _vector_cache(path):
    with _vector_caches_lock:
        cache = _vector_caches.get(path)
        if cache is None:
            cache = _vector_caches[path] = _VectorCache()
        return cache


def _to_blob(v):
    return np.asarray(v, dtype=np.float32).tobytes()


def _from_blob(b):
    return None if b is None else np.frombuffer(b, dtype=np.float32)


def _where(metadata):
    if not metadata:
        return "", []
    clauses, params = [], []
    for key, value in metadata.items():
        if key.startswith("$") or isinstance(value, dict):
            raise NotImplementedError("sqlite state backend supports equality metadata filters only ({'key': value})")
        clauses.append("json_extract(metadata, ?) = ?")
        params += [f'$."{key}"', value]
    return "WHERE " + " AND ".join(clauses), params


class SQLiteStateClient(StateClient):
    def __init__(self, agent_name,
                 module_name:str=None,
                 embedder:str="default",
                 embedding_custom_function:chromadb.EmbeddingFunction=None,
                 data_dir:str=None,
                 backend:str="sqlite"):
        self.agent_name = agent_name
        self.module_name = module_name
        self._embedding_function = _make_embedding_function(embedder, embedding_custom_function)
        data_dir = data_dir or DEFAULT_DATA_DIR
        os.makedirs(data_dir, exist_ok=True)
        self.path = os.path.abspath(os.path.join(data_dir, f"{agent_name}.sqlite"))
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, timeout=30, check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.executescript(_SCHEMA)
        self._cache = _vector_cache(self.path)

    def _execute(self, sql, params=()):
        with self._lock:
            return self._conn.execute(sql, params).fetchall()

    # --- write -------------------------------------------------------------

    def add(self,
            states:str|list,
            timestamp:float|datetime.datetime=None,
            metadata:dict=None):
        if type(states) == str:
            states = [states]
        if timestamp is None:
            timestamp = datetime.datetime.now().timestamp()
        elif type(timestamp) == datetime.datetime:
            timestamp = timestamp.timestamp()
        meta = json.dumps(metadata or {}, ensure_ascii=False)
        rows = [(str(uuid.uuid4()), float(timestamp), self.module_name, s, meta) for s in states]
        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                self._conn.executemany(
                    "INSERT INTO states (id, ts, module, text, metadata) VALUES (?, ?, ?, ?, ?)", rows)
                self._conn.execute("COMMIT")
            except BaseException:
                self._conn.execute("ROLLBACK")
                raise

    def delete(self, ids: str | list[str]):
        if isinstance(ids, str):
            ids = [ids]
        with self._lock:
            self._conn.executemany("DELETE FROM states WHERE id = ?", [(i,) for i in ids])
        with self._cache.lock:
            self._cache.reset()

    def clear(self):
        with self._lock:
            self._conn.execute("DELETE FROM states")
        with self._cache.lock:
            self._cache.reset()

    # --- read --------------------------------------------------------------

    def count(self):
        return self._execute("SELECT COUNT(*) FROM states")[0][0]

    def last_seq(self):
        """seq of the newest row (0 if empty). Pass it to get(since_seq=...) later to read only what came after."""
        return self._execute("SELECT COALESCE(MAX(seq), 0) FROM states")[0][0]

    def get(self, max_count:int=None, metadata:dict=None, reverse:bool=False, since_seq:int=None):
        where, params = _where(metadata)
        if since_seq is not None:
            where = (where + " AND " if where else "WHERE ") + "seq > ?"
            params.append(int(since_seq))
        order = "ASC" if reverse else "DESC"
        sql = f"SELECT seq, id, ts, module, text, metadata, vector FROM states {where} ORDER BY ts {order}, seq {order}"
        if max_count is not None and max_count > 0:
            sql += " LIMIT ?"
            params.append(int(max_count))
        return self._rows_to_state(self._execute(sql, params))

    def get_legacy(self, max_count:int=None, metadata:dict=None, reverse:bool=False):
        return self.get(max_count=max_count, metadata=metadata, reverse=reverse)

    def query(self, query_text:str, max_count:int=10, return_distances:bool=False, metadata:dict=None):
        self.embed_pending()
        q = np.asarray(self._embedding_function([query_text])[0], dtype=np.float32)
        with self._cache.lock:
            self._refresh_cache()
            seqs, vectors = self._cache.seqs, self._cache.vectors
        if metadata:
            where, params = _where(metadata)
            allowed = np.array([r[0] for r in self._execute(f"SELECT seq FROM states {where}", params)], dtype=np.int64)
            mask = np.isin(seqs, allowed)
            seqs = seqs[mask]
            vectors = vectors[mask] if vectors is not None else None
        if vectors is None or len(seqs) == 0:
            state = self._rows_to_state([])
            return (state, []) if return_distances else state
        # squared L2, the same distance Chroma uses by default
        d = np.sum((vectors - q) ** 2, axis=1)
        k = min(max_count, len(d)) if max_count and max_count > 0 else len(d)
        top = np.argsort(d, kind="stable")[:k]
        chosen = [int(seqs[i]) for i in top]
        placeholders = ",".join("?" * len(chosen))
        rows = {r[0]: r for r in self._execute(
            f"SELECT seq, id, ts, module, text, metadata, vector FROM states WHERE seq IN ({placeholders})", chosen)}
        ordered = [rows[s] for s in chosen if s in rows]
        state = self._rows_to_state(ordered)
        if return_distances:
            return state, [float(d[i]) for i, s in zip(top, chosen) if s in rows]
        return state

    def embed_pending(self, limit:int=None):
        """Embed rows that have no vector yet. Returns how many were embedded.
        A failed embedding call is warned about and left for the next time; no state is lost."""
        done = 0
        while limit is None or done < limit:
            n = EMBED_BATCH if limit is None else min(EMBED_BATCH, limit - done)
            rows = self._execute("SELECT seq, text FROM states WHERE vector IS NULL ORDER BY seq LIMIT ?", (n,))
            if not rows:
                break
            try:
                vectors = self._embedding_function([r[1] for r in rows])
            except Exception as e:
                warnings.warn(f"state embedding failed, will retry later: {e}")
                break
            with self._lock:
                self._conn.executemany("UPDATE states SET vector = ? WHERE seq = ?",
                                       [(_to_blob(v), r[0]) for v, r in zip(vectors, rows)])
            done += len(rows)
        return done

    def _refresh_cache(self, _retry=True):
        # caller holds self._cache.lock
        # A delete/clear from another client in the same process resets the cache directly;
        # one from another process is caught by the row count check below.
        rows = self._execute(
            "SELECT seq, vector FROM states WHERE vector IS NOT NULL AND seq > ? ORDER BY seq",
            (self._cache.max_seq,))
        if rows:
            new_seqs = np.array([r[0] for r in rows], dtype=np.int64)
            new_vecs = np.stack([_from_blob(r[1]) for r in rows])
            if self._cache.vectors is None:
                self._cache.seqs, self._cache.vectors = new_seqs, new_vecs
            else:
                self._cache.seqs = np.concatenate([self._cache.seqs, new_seqs])
                self._cache.vectors = np.concatenate([self._cache.vectors, new_vecs])
            self._cache.max_seq = int(new_seqs[-1])
        embedded = self._execute(
            "SELECT COUNT(*) FROM states WHERE vector IS NOT NULL AND seq <= ?", (self._cache.max_seq,))[0][0]
        if embedded != len(self._cache.seqs) and _retry:
            self._cache.reset()
            self._refresh_cache(_retry=False)

    def _rows_to_state(self, rows):
        n = len(rows)
        vectors = [_from_blob(r[6]) for r in rows]
        if n and all(v is not None for v in vectors) and len({v.shape for v in vectors}) == 1:
            vector = np.stack(vectors)
        else:
            vector = np.empty(n, dtype=object)
            for i, v in enumerate(vectors):
                vector[i] = v
        return State(
            ids=[r[1] for r in rows],
            texts=[r[4] for r in rows],
            vector=vector,
            timestamps=[r[2] for r in rows],
            metadata=[json.loads(r[5]) for r in rows],
            seqs=[r[0] for r in rows],
            modules=[r[3] for r in rows],
        )

    def dump(self, file_path:str):
        rows = self._execute("SELECT seq, id, ts, module, text, metadata, vector FROM states ORDER BY seq")
        all_docs = {
            "ids": [r[1] for r in rows],
            "documents": [r[4] for r in rows],
            "metadatas": [dict(json.loads(r[5]), timestamp=r[2]) for r in rows],
            "embeddings": [None if r[6] is None else _from_blob(r[6]).tolist() for r in rows],
        }
        if file_path.endswith(".pkl") or file_path.endswith(".pickle"):
            with open(file_path, "wb") as f:
                pickle.dump(all_docs, f)
        elif file_path.endswith(".json"):
            with open(file_path, "w") as f:
                json.dump(all_docs, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError("Unsupported file format. Use .pkl, .pickle, or .json.")

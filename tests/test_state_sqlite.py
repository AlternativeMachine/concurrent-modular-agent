import threading, time
import numpy as np
import pytest
import test_state
from concurrent_modular_agent import StateClient
from concurrent_modular_agent.state.sqlite_client import SQLiteStateClient


@pytest.fixture(autouse=True)
def sqlite_backend(monkeypatch, tmp_path):
    """Run every test in test_state.py again on the sqlite backend."""
    def factory(agent_name, *args, **kwargs):
        kwargs.setdefault("data_dir", str(tmp_path))
        kwargs["backend"] = "sqlite"
        return StateClient(agent_name, *args, **kwargs)
    monkeypatch.setattr(test_state, "StateClient", factory)


for _name in dir(test_state):
    if _name.startswith("test_") and _name != "test_state_0":
        globals()[f"{_name}_on_sqlite"] = getattr(test_state, _name)


class CountingEmbedder:
    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail

    def __call__(self, input):
        self.calls += 1
        if self.fail:
            raise RuntimeError("embedding service down")
        return [[float(len(t)), float(t.count("a")), 1.0] for t in input]


def test_backend_dispatch(tmp_path):
    s = StateClient("a", "m", embedder="none", data_dir=str(tmp_path), backend="sqlite")
    assert isinstance(s, SQLiteStateClient)
    assert isinstance(s, StateClient)
    with pytest.raises(ValueError):
        StateClient("a", embedder="none", backend="nope")


def test_add_does_not_embed_and_survives_embedding_failure(tmp_path):
    emb = CountingEmbedder(fail=True)
    s = StateClient("a", "m", embedder="custom", embedding_custom_function=emb, data_dir=str(tmp_path), backend="sqlite")
    s.add(["x", "y"])
    assert emb.calls == 0
    with pytest.warns(UserWarning):
        assert s.embed_pending() == 0
    assert s.count() == 2
    assert s.get()[0].vector is None
    emb.fail = False
    assert s.embed_pending() == 2
    assert s.get()[0].vector is not None


def test_query_embeds_lazily_and_ranks(tmp_path):
    emb = CountingEmbedder()
    s = StateClient("a", "m", embedder="custom", embedding_custom_function=emb, data_dir=str(tmp_path), backend="sqlite")
    s.add(["aaaa", "b", "aab"])
    st, dist = s.query("aaaa", max_count=2, return_distances=True)
    assert st[0].text == "aaaa"
    assert dist[0] == 0.0
    assert len(st) == 2
    s.add("aaab")
    assert s.query("aaab", max_count=1)[0].text == "aaab"


def test_seq_module_and_since(tmp_path):
    a = StateClient("a", "vision", embedder="none", data_dir=str(tmp_path), backend="sqlite")
    b = StateClient("a", "hearing", embedder="none", data_dir=str(tmp_path), backend="sqlite")
    a.add("seen", timestamp=10)
    mark = a.last_seq()
    b.add("heard", timestamp=10)
    a.add("seen again", timestamp=10)
    s = a.get()
    assert [r.text for r in s] == ["seen again", "heard", "seen"]  # same timestamp: newest insert first
    assert [r.module for r in s] == ["vision", "hearing", "vision"]
    new = b.get(since_seq=mark, reverse=True)
    assert [r.text for r in new] == ["heard", "seen again"]
    assert new[0].seq == mark + 1


def test_metadata_filter_equality_only(tmp_path):
    s = StateClient("a", embedder="none", data_dir=str(tmp_path), backend="sqlite")
    s.add("x", metadata={"kind": "speech", "n": 1})
    s.add("y", metadata={"kind": "vision", "n": 1})
    assert [r.text for r in s.get(metadata={"kind": "speech", "n": 1})] == ["x"]
    with pytest.raises(NotImplementedError):
        s.get(metadata={"$or": [{"kind": "speech"}]})


def test_concurrent_writers(tmp_path):
    def writer(i):
        c = StateClient("a", f"m{i}", embedder="none", data_dir=str(tmp_path), backend="sqlite")
        for j in range(200):
            c.add(f"{i}-{j}")
            c.get(max_count=10)
    threads = [threading.Thread(target=writer, args=(i,)) for i in range(6)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert StateClient("a", embedder="none", data_dir=str(tmp_path), backend="sqlite").count() == 1200


def test_get_latest_does_not_scale_with_size(tmp_path):
    s = StateClient("a", embedder="none", data_dir=str(tmp_path), backend="sqlite")
    s.add([f"s{i}" for i in range(100_000)])
    t = time.perf_counter()
    for _ in range(100):
        r = s.get(max_count=10)
    per_call = (time.perf_counter() - t) / 100
    assert r[0].text == "s99999"
    assert per_call < 0.01


def test_delete_and_clear_reset_query_cache(tmp_path):
    emb = CountingEmbedder()
    s = StateClient("a", embedder="custom", embedding_custom_function=emb, data_dir=str(tmp_path), backend="sqlite")
    s.add(["aaaa", "b"])
    top = s.query("aaaa", max_count=1)[0]
    s.delete(top.id)
    assert s.query("aaaa", max_count=1)[0].text == "b"
    s.clear()
    assert len(s.query("aaaa")) == 0

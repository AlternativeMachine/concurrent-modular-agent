import chromadb
import numpy as np
from .state import State

def _convert_ndarrays_to_lists(data):
    # embeddingsをlistに変換
    if "embeddings" in data and data["embeddings"] is not None:
        data["embeddings"] = [e.tolist() if isinstance(e, np.ndarray) else e for e in data["embeddings"]]
    return data

def _get_client(directory:str=None):
    if directory is None:
        chromadb_client = chromadb.HttpClient(host='localhost', port=8000)
    else:
        chromadb_client = chromadb.PersistentClient(path=directory)
    return chromadb_client

def _convert_chromadb_data_to_state(data):
    ids = data['ids']
    texts = data['documents']
    vector = data['embeddings']
    metadata = data['metadatas']
    timestamps = []
    metadata = []
    for m in data['metadatas']:
        timestamps.append(m['timestamp'])
        m.pop('timestamp')
        metadata.append(m)
    state = State(
        ids=ids,
        texts=texts,
        vector=vector,
        timestamps=timestamps,
        metadata=metadata
    )
    return state
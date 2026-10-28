import os, datetime, uuid
import numpy as np
from loguru import logger
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from dataclasses import dataclass
import warnings
import datetime

@dataclass
class StateRecord:
    id: str
    text: str
    vector: np.ndarray
    timestamp: float
    metadata: dict
    seq: int = None
    module: str = None
    

class State:
    def __init__(self, ids, texts, vector, timestamps, metadata=None, seqs=None, modules=None):
        if len(ids) != len(texts) or len(ids) != len(vector) or len(ids) != len(timestamps):
            raise ValueError("The length of ids, texts, vectors, and timestamps must be the same.")
        if metadata is not None and len(ids) != len(metadata):
            raise ValueError("The length of ids, texts, vectors, timestamps, and metadata must be the same.")
        if metadata is None:
            metadata = [{} for i in range(len(ids))]
        if isinstance(ids, np.ndarray):
            ids = ids.tolist()
        if isinstance(texts, np.ndarray):
            texts = texts.tolist()
        if isinstance(timestamps, np.ndarray):
            timestamps = timestamps.tolist()
        if isinstance(metadata, np.ndarray):
            metadata = metadata.tolist()
        self.ids = ids
        self.texts = texts
        self.vector = np.array(vector)  # Ensure vector is a NumPy array
        self.timestamps = timestamps
        self.metadata = metadata
        # Only the sqlite backend fills these (insertion order and the module that wrote each state).
        self.seqs = seqs
        self.modules = modules
    
    def __len__(self):
        return len(self.ids)

    def __getitem__(self, i):
        if isinstance(i, int):  # 単一の整数インデックス
            return StateRecord(
                id=self.ids[i],
                text=self.texts[i],
                vector=self.vector[i],
                timestamp=self.timestamps[i],
                metadata=self.metadata[i],
                seq=None if self.seqs is None else self.seqs[i],
                module=None if self.modules is None else self.modules[i],
            )
        elif isinstance(i, (list, tuple, np.ndarray)):  # リスト、タプル、NumPy配列
            indices = np.array(i, dtype=int)  # NumPy配列に変換
            return State(
                ids=[self.ids[idx] for idx in indices],
                texts=[self.texts[idx] for idx in indices],
                vector=self.vector[indices],
                timestamps=[self.timestamps[idx] for idx in indices],
                metadata=[self.metadata[idx] for idx in indices],
                seqs=None if self.seqs is None else [self.seqs[idx] for idx in indices],
                modules=None if self.modules is None else [self.modules[idx] for idx in indices],
            )
        elif isinstance(i, slice):  # スライス
            return State(
                ids=self.ids[i],
                texts=self.texts[i],
                vector=self.vector[i],
                timestamps=self.timestamps[i],
                metadata=self.metadata[i],
                seqs=None if self.seqs is None else self.seqs[i],
                modules=None if self.modules is None else self.modules[i],
            )
        else:
            raise TypeError("Indexing must be an integer, list, tuple, NumPy array, or slice.")


import os, datetime, uuid, pickle, json
import numpy as np
from loguru import logger
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from dataclasses import dataclass
import warnings
import datetime
from .state import State
from .custom_embedder import CustomEmbeddingFunction, DummyEmbeddingFunction

def _convert_ndarrays_to_lists(data):
    # embeddingsをlistに変換
    if "embeddings" in data and data["embeddings"] is not None:
        data["embeddings"] = [e.tolist() if isinstance(e, np.ndarray) else e for e in data["embeddings"]]
    return data


class StateClient():
    def __init__(self, agent_name, module_name:str=None, embedder:str="default", embedding_custom_function:chromadb.EmbeddingFunction=None):
        self._chromadb_client = chromadb.HttpClient(host='localhost', port=8000)
        if embedder == "default":
            warnings.warn("\033[91mThe 'default' embedder is no longer OpenAI embedder. Please specify 'openai' or 'gemma' for using predefined embedders, or 'custom' to use embedding_custom_function.\033[0m", DeprecationWarning)
            self._embedding_function = embedding_functions.DefaultEmbeddingFunction()
            pass
        elif embedder == "openai":
            self._embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key_env_var="OPENAI_API_KEY",
                model_name="text-embedding-3-small"
            )
        elif embedder == "gemma":
            self._embedding_function = CustomEmbeddingFunction(
                model_id="google/embeddinggemma-300M",
                device="cpu",
                truncate_dim=128
            )
        elif embedder == "none":
            self._embedding_function = DummyEmbeddingFunction()
        else:
            if embedding_custom_function is None:
                raise ValueError("When embedder_option is 'custom', embedding_custom_function must be provided.")
            self._embedding_function = embedding_custom_function
        self._chromadb_collection = self._chromadb_client.get_or_create_collection(
            self._convert_agent_name_2_collection_name(agent_name),
            embedding_function=self._embedding_function
        )

    @staticmethod
    def _convert_agent_name_2_collection_name(agent_name):
        return f"{__package__.split('.')[0]}-state-{agent_name}"
    
    @staticmethod
    def _convert_collection_name_2_agent_name(collection_name):
        if collection_name.startswith(f"{__package__.split('.')[0]}-state-"):
            return collection_name.replace(f"{__package__.split('.')[0]}-state-", "")
        else:
            raise ValueError(f"Invalid collection name: {collection_name}. It should start with '{__package__.split('.')[0]}-state-'")
    
    def add(self, 
            states:str|list, 
            timestamp:float|datetime.datetime=None, 
            metadata:dict=None):
        if type(states) == str:
            states = [states]
        n = len(states)
        ids = [str(uuid.uuid4()) for i in range(n)]
        if timestamp is None:
            now = datetime.datetime.now().timestamp()
            timestamps = [now for i in range(n)]
        else:
            if type(timestamp) == datetime.datetime:
                timestamp = timestamp.timestamp()
            timestamps = [timestamp for i in range(n)]
        metadatas = [{'timestamp': t} for t in timestamps]
        if metadata is not None:
            for m in metadatas:
                m.update(metadata)
        try:
            self._chromadb_collection.add(ids=ids, documents=states, metadatas=metadatas)
        except Exception as e:
            print(f"Error adding states: {e}")

    def get(self, max_count:int=None, metadata:dict=None, reverse:bool=False):
        if metadata is None:
            data = self._chromadb_collection.get(include=['metadatas'])
        else:
            data = self._chromadb_collection.get(include=['metadatas'], where=metadata)
        ids = np.array(data['ids'])
        if len(ids) == 0:
            return State(
                ids=[],
                texts=[],
                vector=[],
                timestamps=[],
                metadata=[]
            )
        timestamps = [d['timestamp'] for d in data['metadatas']]
        ids = ids[np.argsort(timestamps, kind='stable')]
        if not reverse:
            ids = ids[::-1]
        if max_count is not None and max_count > 0:
            ids = ids[:max_count]
        data = self._chromadb_collection.get(ids=ids.tolist(), include=['embeddings', 'documents', 'metadatas'])
        state = self._convert_chromadb_data_to_state(data)
        index = np.argsort(state.timestamps, kind='stable')[::-1]
        state = state[index]
        if reverse:
            state = state[::-1]
        if max_count is not None and max_count > 0:
            state = state[:max_count]
        return state

    def get_legacy(self, max_count:int=None, metadata:dict=None, reverse:bool=False):
        if metadata is None:
            data = self._chromadb_collection.get(include=['embeddings', 'documents', 'metadatas'])
        else:
            data = self._chromadb_collection.get(include=['embeddings', 'documents', 'metadatas'], where=metadata)
        state = self._convert_chromadb_data_to_state(data)
        index = np.argsort(state.timestamps, kind='stable')[::-1]
        state = state[index]
        if reverse:
            state = state[::-1]
        if max_count is not None and max_count > 0:
            state = state[:max_count]
        return state

    def query(self, query_text:str, max_count:int=10, return_distances:bool=False, metadata:dict=None):
        query_include = ['embeddings', 'documents', 'metadatas']
        if return_distances:
            query_include.append('distances')
        if metadata is None:
            data = self._chromadb_collection.query(query_texts=query_text, n_results=max_count, include=query_include)
        else:
            data = self._chromadb_collection.query(query_texts=query_text, n_results=max_count, include=query_include, where=metadata)
                                               
        ids = data['ids'][0]
        texts = data['documents'][0]
        vector = data['embeddings'][0]
        timestamps = []
        metadata = []
        for m in data['metadatas'][0]:
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
        if return_distances:
            return state, data['distances'][0]
        else:
            return state

    def delete(self, ids: str | list[str]):
        if isinstance(ids, str):
            ids = [ids]
        try:
            self._chromadb_collection.delete(ids=ids)
        except Exception as e:
            print(f"Error deleting ids {ids}: {e}")

    def count(self):
        n = self._chromadb_collection.count()
        return n
    
    def clear(self):
        collection_name = self._chromadb_collection.name
        self._chromadb_client.delete_collection(collection_name)
        self._chromadb_collection = self._chromadb_client.create_collection(
            collection_name,
            embedding_function=self._embedding_function
        )

    @staticmethod
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
    
    def latest(self, max_count:int=10):
        warnings.warn("The 'latest' method is deprecated, use 'get' method instead.", DeprecationWarning)
        return self.get(max_count=max_count)

    def retrieve(self, query_text:str, max_count:int=10, metadata:dict=None):
        warnings.warn("The 'retrieve' method is deprecated, use 'query' method instead.", DeprecationWarning)
        return self.query(query_text=query_text, max_count=max_count, metadata=metadata)

    def backup(self, file_path:str):
        all_docs = self._chromadb_collection.get(include=["metadatas", "documents", "embeddings"])

        if file_path.endswith(".pkl") or file_path.endswith(".pickle"):
            # バイナリ形式で保存
            with open(file_path, "wb") as f:
                pickle.dump(all_docs, f)
        elif file_path.endswith(".json"):
            # numpy配列をlistに変換
            all_docs = _convert_ndarrays_to_lists(all_docs)
            # JSONファイルに保存
            with open(file_path, "w") as f:
                json.dump(all_docs, f, ensure_ascii=False, indent=2)        
        else:
            raise ValueError("Unsupported file format. Use .pkl, .pickle, or .json.")


    @staticmethod
    def get_all_names():
        chromadb_client = chromadb.HttpClient(host='localhost', port=8000)
        collections = chromadb_client.list_collections()
        agent_memory_list = []
        for collection in collections:
            memory_name = StateClient._convert_collection_name_2_agent_name(collection.name)
            agent_memory_list.append(memory_name)
        return agent_memory_list

    @staticmethod
    def delete_by_name(name):
        chromadb_client = chromadb.HttpClient(host='localhost', port=8000)
        collection_name = StateClient._convert_agent_name_2_collection_name(name)
        try:
            chromadb_client.delete_collection(collection_name)
        except chromadb.errors.NotFoundError:
            raise ValueError(f"Agent memory with the name '{name}' does not exist.")
        
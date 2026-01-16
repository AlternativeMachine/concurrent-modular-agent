from .client import StateClient
import chromadb
from .utils import _get_client

class MemoryManager:
    def __init__(self, directory:str=None):
        self._directory = directory
        self._chromadb_client = _get_client(directory)
        
    def get_state_client(self, name, 
                         module_name:str=None,
                         embedder:str="default", 
                         embedding_custom_function:chromadb.EmbeddingFunction=None):
        return StateClient(
            agent_name=name,
            module_name=module_name,
            embedder=embedder,
            embedding_custom_function=embedding_custom_function,
            data_dir=self._directory
        )

    def get_all_names(self):
        collections = self._chromadb_client.list_collections()
        agent_memory_list = []
        for collection in collections:
            memory_name = StateClient._convert_collection_name_2_agent_name(collection.name)
            agent_memory_list.append(memory_name)
        return agent_memory_list

    def delete_by_name(self, name):
        collection_name = StateClient._convert_agent_name_2_collection_name(name)
        try:
            self._chromadb_client.delete_collection(collection_name)
        except chromadb.errors.NotFoundError:
            raise ValueError(f"Agent memory with the name '{name}' does not exist.")
        
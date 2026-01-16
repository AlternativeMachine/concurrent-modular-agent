from concurrent_modular_agent import Agent
from concurrent_modular_agent.state import StateClient, MemoryManager
import pytest
import tempfile

def test_memory_list():
    agent = Agent('test_name1')
    state = StateClient("test_name2")
    memory_manager = MemoryManager()
    memory_list = memory_manager.get_all_names()
    # for m in memory_list:
        # print(m)
    assert "test_name1" in memory_list, "test_name1 not found in memory list"
    assert "test_name2" in memory_list, "test_name2 not found in memory list"
    # for m in memory_list:
        # print(m)
        
def test_memory_delete():
    state = StateClient("test_name3")
    memory_manager = MemoryManager()
    memory_list = memory_manager.get_all_names()
    assert "test_name3" in memory_list, "test_name3 not found in memory list before deletion"    
    
    # Test deletion of an existing memory
    memory_manager.delete_by_name("test_name3")
    memory_list = memory_manager.get_all_names()
    assert "test_name3" not in memory_list, "test_name3 found in memory list after deletion"
    
    # Test deletion of a non-existent memory
    with pytest.raises(ValueError):
        memory_manager.delete_by_name("test_name3")


import numpy as np
import json
import pickle

def test_memory_backup():
    state = StateClient("test_name4")
    state.clear()
    for i in range(3):
        state.add("test {i}")
    file_path = tempfile.NamedTemporaryFile(delete=False).name
    state.dump(file_path+".json")
    state.dump(file_path+".pkl")
    
    restored_state_1 = json.load(open(file_path+".json", "r"))
    restored_state_2 = pickle.load(open(file_path+".pkl", "rb"))
    original_state = state.get(max_count=1000, reverse=True)
    # 元のstateと復元されたstateの比較
    for i in range(len(original_state)):
        assert original_state[i].text == restored_state_1['documents'][i], f"Document mismatch at index {i}"
        assert original_state[i].text == restored_state_2['documents'][i], f"Document mismatch at index {i}"
        assert np.all(original_state[i].vector == np.array(restored_state_1['embeddings'][i])), f"Embedding mismatch at index {i}"
        assert np.all(original_state[i].vector == np.array(restored_state_2['embeddings'][i])), f"Embedding mismatch at index {i}"
        assert original_state[i].timestamp == restored_state_1['metadatas'][i]['timestamp'], f"Timestamp mismatch at index {i}"
        assert original_state[i].timestamp == restored_state_2['metadatas'][i]['timestamp'], f"Timestamp mismatch at index {i}"
        assert original_state[i].id == restored_state_1['ids'][i], f"ID mismatch at index {i}"
        assert original_state[i].id == restored_state_2['ids'][i], f"ID mismatch at index {i}"

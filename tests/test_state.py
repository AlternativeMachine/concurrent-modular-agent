from concurrent_modular_agent import StateClient
from concurrent_modular_agent.state import State
import numpy as np

def test_state_metadata():
    state = StateClient("test_agent")
    state.clear()
    state.add("state 1", metadata={"tag": "tag1"})
    state.add("state 2", metadata={"tag": "tag2"})
    state.add("state 3", metadata={"meta": "meta"})
    assert state.count() == 3
    s = state.get()
    assert len(s) == 3
    assert s[0].metadata["meta"] == "meta"
    assert s[1].metadata["tag"] == "tag2"
    assert s[2].metadata["tag"] == "tag1"
    s = state.query("1", max_count=1)
    assert len(s) == 1
    assert s[0].metadata["tag"] == "tag1"

def test_state_metadata_get():
    state = StateClient("test_agent")
    state.clear()
    state.add("state 1", metadata={"tag": "tag1"})
    state.add("state 2", metadata={"tag": "tag1"})
    state.add("state 3", metadata={"tag": "tag2"})
    s = state.get(metadata={"tag": "tag1"})
    assert len(s) == 2
    assert s[0].metadata["tag"] == "tag1"
    assert s[0].text == "state 2"
    assert s[1].metadata["tag"] == "tag1"
    assert s[1].text == "state 1"

def test_state_metadata_query():
    state = StateClient("test_agent")
    state.clear()
    state.add("hello", metadata={"tag": "tag1"})
    state.add("world", metadata={"tag": "tag1"})
    state.add("hello", metadata={"tag": "tag2"})
    state.add("world", metadata={"tag": "tag2"})
    s = state.query("hello", metadata={"tag": "tag1"})
    assert len(s) == 2
    assert s[0].metadata["tag"] == "tag1"
    assert s[0].text == "hello"
    assert s[1].metadata["tag"] == "tag1"
    assert s[1].text == "world"
    s = state.query("hello", metadata={"tag": "tag2"})
    assert len(s) == 2
    assert s[0].metadata["tag"] == "tag2"
    assert s[0].text == "hello"
    assert s[1].metadata["tag"] == "tag2"
    assert s[1].text == "world"
       
def test_state_0():
    ids = ["id0", "id1", "id2", "id3", "id4"]
    texts = ["text0", "text1", "text2", "text3", "text4"]
    vector = np.random.rand(5, 10)  # 5つの10次元ベクトル
    timestamps = [0.0, 1.0, 2.0, 3.0, 4.0]
    state = State(ids, texts, vector, timestamps)
    assert state[1].text == "text1"
    assert len(state[[1, 3, 4]]) == 3
    assert state[[1, 3, 4]][1].text == "text3"

def test_state_1():
    state = StateClient("test_agent")
    state.clear()
    assert state.count() == 0
    state.add("aaaa")
    assert state.count() == 1
    
def test_state_2():
    state = StateClient("test_agent")
    state_num = state.count()
    state.add("aaaa")
    assert state.count() == state_num + 1
    s = state.get(max_count=10)
    assert s[0].text == "aaaa"

def test_state_3():
    state = StateClient("test_agent")
    state.clear()
    state.add("concurrent modular agent.")
    state.add("hell world")
    state.add("hogehoge")
    assert state.count() == 3
    s = state.query("test_agent", max_count=1)
    assert len(s)== 1
    assert s[0].text == "concurrent modular agent."
    
def test_state_4():
    state = StateClient("test_agent")
    state.clear()
    new_states = []
    for i in range(100):
        new_states.append(f"state {i}")
    state.add(new_states)
    state.add('state new')
    assert state.count() == 101
    s = state.get(max_count=1)
    assert s[0].text == 'state new'

def test_state_5():
    state = StateClient("test_agent")
    state.clear()
    s = state.get()
    assert len(s) == 0

def test_state_6():
    state = StateClient("test_agent")
    state.clear()
    new_states = []
    for i in range(100):
        new_states.append(f"state {i}")
    state.add(new_states)
    s = state.get(max_count=-1)
    assert len(s) == 100
    s = state.get(max_count=None)
    assert len(s) == 100

def test_state_huge_data():
    state = StateClient("test_agent_none", embedder="none")
    state.clear()
    new_states = []
    N = 100
    for i in range(N):
        new_states.append(f"state {i}")
    state.add(new_states)
    s = state.get()
    assert len(s) == N
    s = state.get(max_count=10)
    assert len(s) == 10
    assert s[0].text == "state 99"

import datetime
def test_state_datetime_1():
    state = StateClient("test_agent")
    state.clear()
    state.add("3", timestamp=datetime.datetime(2025, 1, 3))
    state.add("1", timestamp=datetime.datetime(2025, 1, 1))
    state.add("2", timestamp=datetime.datetime(2025, 1, 2))
    s = state.get(max_count=3)
    assert s[0].text == "3"
    assert s[1].text == "2"
    assert s[2].text == "1"

def test_state_datetime_2():
    state = StateClient("test_agent")
    state.clear()
    state.add("3", timestamp=3)
    state.add("1", timestamp=1)
    state.add("2", timestamp=2)
    s = state.get(max_count=3)
    assert s[0].text == "3"
    assert s[1].text == "2"
    assert s[2].text == "1"    
    
def test_state_delete_single():
    state = StateClient("test_agent")
    state.clear()
    state.add("state 1")
    state.add("state 2")
    state.add("state 3")
    assert state.count() == 3
    s = state.get()
    target_record = next(rec for rec in s if rec.text == "state 2")
    target_id = target_record.id
    state.delete(target_id)
    s_after = state.get()
    texts_after = [rec.text for rec in s_after]
    assert state.count() == 2
    assert "state 2" not in texts_after
    assert "state 1" in texts_after
    assert "state 3" in texts_after

def test_none_embedder():
    state = StateClient("test_agent_none", embedder="none")
    state.clear()
    state.add("state 1", metadata={"tag": "tag1"})
    state.add("state 2", metadata={"tag": "tag1"})
    state.add("state 3", metadata={"tag": "tag2"})
    s = state.get(metadata={"tag": "tag1"})
    assert len(s) == 2
    assert s[0].metadata["tag"] == "tag1"
    assert s[0].text == "state 2"
    assert s[1].metadata["tag"] == "tag1"
    assert s[1].text == "state 1"
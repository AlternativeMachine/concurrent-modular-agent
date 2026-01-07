from concurrent_modular_agent import StateClient
import pytest

@pytest.fixture
def state():
    state = StateClient("test_retriever", "main", embedder="default", embedding_custom_function=None)
    state.clear()
    state.add("I like apple.", timestamp=0)
    state.add("I like banana.", timestamp=1)
    state.add("I like cherry.", timestamp=2)
    state.add("I like date.", timestamp=3)
    state.add("I like eggplant.", timestamp=4)
    state.add("I like fig.", timestamp=5)
    return state

from concurrent_modular_agent import OldestRetriever, LatestRetriever, TimeWeightedRetriever

def test_oldest_retriever(state):
    retriever = OldestRetriever(state)
    s = retriever.retrieve(max_count=3)
    assert len(s) == 3
    assert s[0].text == "I like apple."
    assert s[1].text == "I like banana."
    assert s[2].text == "I like cherry."

def test_latest_retriever(state):
    retriever = LatestRetriever(state)
    s = retriever.retrieve(max_count=3)
    assert len(s)== 3
    assert s[0].text == "I like fig."
    assert s[1].text == "I like eggplant."
    assert s[2].text == "I like date."

def test_time_weighted_retriever(state):
    # No decay: select the most relevant one even if it is the old.
    retriever = TimeWeightedRetriever(state, decay_rate=0)
    s = retriever.retrieve('apple', max_count=1, now=3)
    assert s[0].text == "I like apple."
    # Strong decay: select the latest one even if it is not relevant.
    retriever = TimeWeightedRetriever(state, decay_rate=1)
    s = retriever.retrieve('apple', max_count=1, now=3)
    assert s[0].text == "I like fig."

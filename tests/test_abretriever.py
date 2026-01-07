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

from concurrent_modular_agent.retriever import AlphaBetaRetriever
import string
import random

def test_alphabeta_retriever(state):
    abretriever = AlphaBetaRetriever(state, alpha=1.0, beta=1.0, pi=0.5)
    # additional_states = []
    # for _ in range(10):
    #     thing_to_memorize = "".join([string.ascii_letters[random.randint(0, len(string.ascii_letters) - 1)] for i in range(10)])
    #     additional_states.append(thing_to_memorize)
    #     state.add(thing_to_memorize)
    s = abretriever.retrieve(query_text="I like fruit.", retrieve_max_count=3)
    assert len(s) == 3
    assert all([ref_count > 0 for ref_count in abretriever.reference_count.values()])


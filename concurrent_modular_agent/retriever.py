from concurrent_modular_agent import StateClient
from concurrent_modular_agent.state import State
from abc import abstractmethod
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple

class BaseRetriever:
    def __init__(self, state: StateClient):
        self.state = state
        
    @abstractmethod
    def retrieve(self, state: StateClient) -> State:
        raise NotImplementedError()


class LatestRetriever(BaseRetriever):
    def retrieve(self, max_count=1):
        latest = self.state.get(max_count=max_count)
        return latest

class OldestRetriever(BaseRetriever):
    def retrieve(self, max_count=1):
        oldest = self.state.get(max_count=max_count, reverse=True)
        return oldest

class TimeWeightedRetriever(BaseRetriever):
    def __init__(self, state, decay_rate):
        super().__init__(state)
        self.decay_rate = decay_rate
        
    def retrieve(self, 
                 query_text:str, 
                 max_count=1, 
                 now:float|datetime=None):
        query_max_count = 100
        all_state, distances = self.state.query(query_text, 
                                                max_count=query_max_count,
                                                return_distances=True)
        if now is None:
            now = datetime.now().timestamp()
        if type(now) == datetime:
            now = now.timestamp()
        
        distances = np.array(distances)
        time_diff = now - np.array(all_state.timestamps)
        timeweighted_distances = distances * np.exp(time_diff*self.decay_rate) # exponential cecay
        # TODO: Implement linear decay
        # timeweighted_distances = distances * (1 + time_diff*self.decay_rate)   # linear decay
        index = np.argsort(timeweighted_distances)
        timeweighted_states = all_state[index]
        if max_count is not None and max_count > 0:
            timeweighted_states = timeweighted_states[:max_count]
        return timeweighted_states

class AlphaBetaRetriever(BaseRetriever):
    """
    Alpha-Beta retrieval strategy.
    This retriever combines social inheritance and self-inheritance to select states based on their popularity and similarity to the query.
    The weights of social inheritance (P_social) and self-inheritance (P_self) are defined as follows:
    P_social = exp(alpha * (reference_count / sum(reference_count)) )
    P_self = exp(beta * distance(query, state))
    P_combined = pi * P_social + (1 - pi) * P_self
    where alpha, beta, and pi are parameters that control the influence of social and self inheritance.
    """
    def __init__(self, state, alpha=1.0, beta=1.0, pi=0.5):
        super().__init__(state)
        self.alpha: float = alpha
        self.beta: float = beta
        self.pi: float = pi

        self.reference_count: Dict[int, int] = {}
    
    def update_params(self, alpha: float = None, beta: float = None, pi: float = None):
        self.alpha = alpha
        self.beta = beta
        self.pi = pi

    def f_social_inheritance(self, X_ref: np.ndarray, alpha: float = None) -> np.ndarray:
        """
        Calculate the social-inheritance weight.
        X_ref: Array of reference counts for all referencible tagsets in the time series.
        alpha: Weighting factor for social inheritance. Positive alpha increases the influence of popular tagsets. Negative alpha increases the influence of unpopular tagsets.
        Returns: Probability distribution over tagsets based on their popularity.
        """
        if alpha is None:
            alpha = self.alpha
        pop_y = X_ref / np.sum(X_ref)
        p_y = np.exp(alpha * pop_y)
        p_y /= np.sum(p_y)
        return p_y

    def f_self_inheritance(self, X_dis: np.ndarray, beta: float = None) -> np.ndarray:
        """
        Calculate the self-inheritance weight.
        X_dis: Array of distances from the starting point context to all other tagsets in the time series.
        beta: Weighting factor for self inheritance. Positive beta increases the influence of similar tagsets. Negative beta increases the influence of dissimilar tagsets.
        Returns: Probability distribution over tagsets based on their similarity to the starting point context.
        """
        if beta is None:
            beta = self.beta
        p_y = np.exp(beta * X_dis)
        p_y /= np.sum(p_y)
        return p_y
        
    def retrieve(self, 
                 query_text: str, 
                 retrieve_max_count: int = 1,
                 query_max_count: int = 100,
                 alpha: float = None,
                 beta: float = None,
                 pi: float = None) -> State:
        query_max_count = 100
        all_state, distances = self.state.query(query_text, 
                                                max_count=query_max_count,
                                                return_distances=True)

        if alpha is None:
            alpha = self.alpha
        if beta is None:
            beta = self.beta
        if pi is None:
            pi = self.pi
        
        distances = np.array(distances)
        reference_counts = np.array([self.reference_count.get(state_id, 1) for state_id in all_state.ids])
        social_inheritance = self.f_social_inheritance(reference_counts, alpha)
        self_inheritance = self.f_self_inheritance(distances, beta)

        combined_scores = pi * social_inheritance + (1 - pi) * self_inheritance
        p_retrieve = combined_scores / np.sum(combined_scores)
        index = np.random.choice(len(all_state.ids), 
                                 size=np.min([retrieve_max_count, len(all_state.ids)]),
                                 replace=False, 
                                 p=p_retrieve)
        ab_states = all_state[index]
        if retrieve_max_count is not None and retrieve_max_count > 0:
            ab_states = ab_states[:retrieve_max_count]
            for state_id in ab_states.ids:
                self.reference_count.setdefault(state_id, 0)
                self.reference_count[state_id] += 1
        return ab_states
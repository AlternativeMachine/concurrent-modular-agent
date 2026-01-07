import multiprocessing, threading, hashlib
from .state import StateClient
from .message import MessageClient
import concurrent_modular_agent as cma

from chromadb import EmbeddingFunction

"""
This class is intended for the mode where agents are launched via the coma CLI interface.
"""
class AgentInterface:
    def __init__(self, agent_name, module_name):
        self.agent_name = agent_name
        self.module_name = module_name
        self.state = StateClient(agent_name, module_name)
        self.message = MessageClient(agent_name, module_name)

        # Generate a color based on agent name and module name
        seed = hashlib.md5(f"{self.agent_name}{self.module_name}".encode()).digest()
        r, g, b = seed[0], seed[1], seed[2]
        self.log_color_code = f"\033[38;2;{r};{g};{b}m"
        self.log_reset_code = "\033[0m"
    @property
    def log_icon(self) -> str:
        """Icon used in log output. Defaults to a gear."""
        return getattr(self, "_log_icon", "⚙️")

    @log_icon.setter
    def log_icon(self, value: str):
        self._log_icon = value if value is not None else "⚙️"

    def log(self, message: str):
        print(f'{self.log_icon} {self.log_color_code}[{self.agent_name}:{self.module_name}]{self.log_reset_code} {message}', flush=True)


"""
This class is intended for the mode where modules are implemented as Python functions and agents are launched from a Python script.
"""
class Agent():
    def __init__(self, name:str, state_embedder:str="default", embedding_custom_function:EmbeddingFunction=None):
        self.name = name
        self.modules = {}
        self.state = StateClient(self.name, 'main', embedder=state_embedder, embedding_custom_function=embedding_custom_function)
        self.message = MessageClient(self.name, 'main')

    def add_module(self, module_name: str, 
                   module_function: callable):
        self.modules[module_name] = module_function
    
    @staticmethod
    def _run_module_process(agent_name, module_name, module_function, initialized_bariier):
        if module_function.__code__.co_argcount == 2:
            state_client = cma.StateClient(agent_name, module_name)
            message_client = cma.MessageClient(agent_name, module_name)
            args = (state_client, message_client)
        elif module_function.__code__.co_argcount == 1:
            agent = AgentInterface(agent_name, module_name)
            args = (agent,)
        else:
            raise TypeError(f"{module_function.__name__} must take 1 (AgentInterface) or 2.  (state_client, message_client) arguments, but got {module_function.__code__.co_argcount} arguments.")
        initialized_bariier.wait()
        module_function(*args)
            
        
    def start(self, detach=True):
        module_processes = []
        # run modules
        initialized_bariier = threading.Barrier(len(self.modules))
        # initialized_bariier = multiprocessing.Barrier(len(self.modules))
        for module_name, module_func in self.modules.items():
            # TODO: Use multiprocessing instead of threading, but it's sometime blocking bug with message passing.
            process = threading.Thread(
            # process = multiprocessing.Process(
                target=self._run_module_process, 
                args=(self.name, module_name, module_func, initialized_bariier))
            
            process.daemon = True
            process.start()
            module_processes.append(process)
            
        if not detach:
            for process in module_processes:
                process.join()
  
        
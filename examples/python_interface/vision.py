from concurrent_modular_agent import Agent
from concurrent_modular_agent import modules

if __name__ == "__main__":
    agent = Agent('vision_example')
    mod = modules.vision(
        device=0,
        prompt="Briefly describe the scene in Japanese.",
        interval=5.0,
        show_window=True,
    )
    agent.add_module("vision_module", mod)
    agent.start(detach=False)

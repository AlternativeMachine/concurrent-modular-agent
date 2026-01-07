import time
from concurrent_modular_agent import AgentInterface, Agent

def sender(agent:AgentInterface):
    i = 0
    while True:
        m = f'hello {i}'
        agent.log(f'send message "{m}"')
        agent.message.send("receiver", m)
        i += 1
        time.sleep(1)

def receiver(agent:AgentInterface):
    while True:
        m = agent.message.receive()
        agent.log(f'received message: "{m}"')
    
agent = Agent('myagent')
agent.add_module("sender", sender)
agent.add_module("receiver", receiver)
agent.start(detach=False)

import time
import concurrent_modular_agent
from concurrent_modular_agent import Agent, StateClient, MessageClient
import random
import string

def memorer(state:StateClient, message:MessageClient):
    i = 0
    while True:
        i += 1
        thing_to_memorize = "".join([string.ascii_letters[random.randint(0, len(string.ascii_letters) - 1)] for i in range(10)])
        state.add(thing_to_memorize, metadata={"module_name": "memorer"})
        m = f"{thing_to_memorize}"
        message.send("recaller", m)
        time.sleep(1)

def recaller(state:StateClient, message:MessageClient):
    while True:
        m = message.receive()
        print(f"[recaller] Received message: {m}")
        in_memory_state, in_memory_distance = state.query(m, max_count=3, return_distances=True, metadata={"module_name": "memorer"})
        output_text = ""
        for text, distance in zip(in_memory_state.texts, in_memory_distance):
            output_text += f"Text: {text}, Distance: {distance}\n"
        output_text += "-------------------------------------------\n"
        print(f"[recaller] Retrieved memories--------------\n{output_text}")

print("This example requires to install the gemma embedder.")
print("Do you want to proceed? (y/n): ", end="")
if input().strip().lower() != "y":
    print("Aborting...")
    exit(1)

agent = Agent('myagent', state_embedder="gemma", embedding_custom_function=None)
agent.add_module("memorer", memorer)
agent.add_module("recaller", recaller)
agent.start(detach=False)

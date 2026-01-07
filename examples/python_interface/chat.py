from openai import OpenAI
from concurrent_modular_agent import Agent, AgentInterface

# This example is still a work in progress and not yet complete.

def chat(agent:AgentInterface):
    openai_client = OpenAI()
    while True:
        m = agent.message.receive()

        messages = [
            {"role": "developer", "content": "あなたは日本語で話すチャットボットです。"},
        ]
        for s in agent.state.latest().texts[::-1]:
            if s.startswith("user_message:"):
                messages.append({"role": "user", "content": s[len("user_message:"):]})
            elif s.startswith("assistant_message:"):
                messages.append({"role": "assistant", "content": s[len("assistant_message:"):]})

        completion = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        output_message = completion.choices[0].message.content
        print(f'ChatBot: {output_message}')
        agent.state.add(f'assistant_message:{output_message}')

        agent.message.send("main", 'finish')  # send signal to main thread for next message
    
    
agent = Agent('chat_agent')
agent.state.clear()
agent.add_module("chat", chat)
agent.start()

# this is main thread work as a module
while True:
    m = input("User: ")
    agent.state.add(f'user_message:{m}')
    agent.message.send("chat", 'reply')  # send signal to chat module
    agent.message.receive()  # wait for signal from chat module

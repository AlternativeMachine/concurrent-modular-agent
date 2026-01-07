# 4. Running the Agent

Let's run the assembly of the modules you have created as an agent!

Actually, running the agent is as simple as running a single command. 

First, make sure you have directory structure like this:

```
my_project/
└── agent1
    ├── user_input.py
    ├── chat.py
    └── memory_organizer.py
```
If you have skipped the previous steps, you can go to `examples/cma_interface` directory.

Also, Docker should be running on your machine, as CMA uses Docker to run the backend services.
```shell
$ coma backend start
```

Then, run the following command in the `my_project` directory:

```shell
$ coma run agent1
```

This command will start the agent named `agent1`, which will automatically load the modules you have created in the `agent1` directory. 
You should see the output similar to this:

```shell
User: 
```

You can now type a message and see how the agent responds.

```console
User: Hi
ChatBot: Hey again! What's new with you?
User: Can I call you CMA agent?
ChatBot: Sure, you can call me CMA agent if you like! It has an intriguing ring to it. What's next on your list?
User: What is your name?
ChatBot: I don't really have a name, but you can call me whatever you like! CMA agent, perhaps? Or maybe something else that suits your fancy.
```

As you can see, the agent remembers the conversation history and responds accordingly. Recall that the user input is retrieved from the memory by the `chat` module, not sent directly to the `chat` module, but still the agent can respond to the user input in a natural way. This means memory is working properly. 

After spent some time chatting with the agent, you can see the existence of the memory more clearly. 

```console
User: What have we talked?
ChatBot: We’ve been chatting about dinosaurs! We started with some imaginative stories about these fascinating prehistoric creatures, like the massive Brachiosaurus and the fierce Tyrannosaurus rex. Then, we moved on to discussing why dinosaurs went extinct, touching on the asteroid impact theory and volcanic activities. If you have anything else you’re curious about, feel free to ask!
```

However, this tutorial did not cover more advanced memory retrieval techniques, such as using similarity search. 
We will cover this in other tutorials later, so stay tuned!

For this getting started tutorial, you have successfully created a simple agent that can chat with the user and remember the conversation history.
Well done!

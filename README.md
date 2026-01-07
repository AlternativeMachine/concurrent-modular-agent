# Concurrent Modular Agent
<img width="1292" alt="cma_architecture" src="https://github.com/user-attachments/assets/65129a59-c37c-4ff4-b4ca-66a33a49226f" />

**Welcome to Concurrent Modular Agent (CoMA) Framework!** 
CoMA is designed to simplify the development of agents that collaborate in a modular and concurrent fashion. It draws inspiration from subsumption architecture, asynchronous message passing in concurrent programming, the global workspace model, and the core software design principles of modularity and reusability.

## Explore the concepts
For a detailed guide on the framework, please refer to our [paper](https://arxiv.org/abs/2508.19042). 

### Core ideas
- **Modularity**: The framework follows a modular design that enables developers to create and integrate various independent modules easily. Each module can be developed, tested, and reused across multiple projects.

- **Concurrency**: The framework supports concurrent execution of multiple modules, allowing them to work in parallel and share information efficiently. This is achieved through two primary mechanisms:
    - **Message Passing**: CoMA employs a message-passing system that supports asynchronous communication, allowing modules to exchange information without tight coupling. (Currently, the message passing is implemented using MQTT protocol)
    - **Shared Memory**: The framework also features a global memory component—--currently implemented as a vector store using Chroma DB--—that lets modules share and retrieve data efficiently. This mechanism is ideal for storing information that may be needed by self or different modules later.


## Installation

### Prerequisites

- **Python 3.12 or Later**  
  This implementation uses the `multiprocessing` and `asyncio` modules available in Python 3.12 and newer.
  
- **Docker**

### Tested Platforms

The framework has been validated on the following platforms:

- **MacOS**  
  - Apple M1 Max (macOS 15.4, Build 24E248)
- **Ubuntu**

### Setup
1. Install docker. 
https://docs.docker.com/engine/install/

2. It is recommended to use a virtual environment. 
```console
$ python -m venv .venv
$ source .venv/bin/activate
```

3. Install the required packages.
```console
$ pip install -e ".[dev]"
```

#### Test
1. Start backend services.
```console
$ coma backend start
```
*Note: You may need to run Docker before starting the backend services.*

You can use the `start`, `stop`, and `restart` commands.

2. Set the OpenAI API Key
```console
$ export OPENAI_API_KEY="your api key"
```

3. Run test.
```console
$ pytest
```

## Start backend services
Run
```console 
$ python -m concurrent_modular_agent.backend start
```

## Examples

There are two modes of running this framework:

1. Declaratively from within Python
2. Via the `coma` CLI interface

These two modes cannot be mixed.

Examples for each mode are available in the `examples` directory.

### Running examples declaratively from within Python

```console
$ python examples/python_interface/chat.py
```

### Running examples via the `coma` CLI interface

```console
$ coma run examples/coma_interface/chat
```
In this mode, hot-reloading of modules is enabled.
Any edits made to files in the folder are reflected immediately without needing to restart the execution.



### CLI `coma` 

```console
$ coma
Usage: coma [OPTIONS] COMMAND [ARGS]...

  CLI tool for concurrent modular agent

Options:
  --help  Show this message and exit.

Commands:
  backend  Backend management commands
  memory   Memory management commands
  run      Run the agent with the specified project directory
```

```console
$ coma memory       
Usage: coma memory [OPTIONS] COMMAND [ARGS]...

  Memory management commands

Options:
  --help  Show this message and exit.

Commands:
  backup  Backup memory to the specified file path
  ls      List memory names
  rm      Delete memory with the specified name
```

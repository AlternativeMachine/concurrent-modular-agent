# 1. Installation

## Prerequisites

Before installing CMA, ensure you have the following prerequisites:

* **Python 3.12 or later**

    CMA uses multiprocessing and asyncio, which are fully supported in Python 3.12 and later versions.

* **Docker**

    CMA uses Docker to run modules (specifically, MQTT for messaging and ChromaDB for vector storage). Ensure you have Docker installed and running on your machine. Please refer to the [Docker installation guide](https://docs.docker.com/get-docker/) for instructions.

## Setup

It is recommended to use a virtual environment:

```console
$ python -m venv .venv
$ source .venv/bin/activate
```

Clone this repository and install the required packages:

```console
$ git clone https://github.com/***.git
$ cd concurrent-modular-agent-main
$ pip install -e ".[dev]"
```

## Testing Your Installation

### 1. Start Backend Services

```console
$ coma backend start
```

**Note:** You need to run Docker before starting the backend services.

**Tip for macOS users:** You need to run the Docker Desktop application, not CLI commands.

You can use the `start`, `stop`, and `restart` commands to manage the backend services. For example, to stop the backend services:

```console
$ coma backend stop
```

### 2. Set Your OpenAI API Key

```console
$ export OPENAI_API_KEY="your_api_key"
```

### 3. Run Tests

```console
$ pytest
```

If all tests pass, you should see output similar to:
```console
....
```

If tests fail, you will see output indicating which tests failed or encountered errors:
```console
..!!!
```

## Next Steps

Now you're ready to start building your agent systems with CMA! Continue to the next section to learn how to create your first project.

<div style="text-align: center; margin: 2rem 0;">
    <a href="../creating-a-new-project" class="indigo-button">
        🚀 Creating Projects
    </a>
</div>

<style>
.indigo-button {
    display: inline-block;
    padding: 12px 32px;
    background-color: #3F51B5;
    color: #FFFFFF !important;
    text-decoration: none !important;
    border-radius: 6px;
    font-weight: 600;
    font-size: 16px;
    box-shadow: 0 3px 6px rgba(63, 81, 181, 0.25);
    transition: all 0.2s ease;
    border: none;
}

.indigo-button:hover {
    background-color: #303F9F;
    box-shadow: 0 4px 8px rgba(63, 81, 181, 0.35);
    transform: translateY(-1px);
    color: #FFFFFF !important;
    text-decoration: none !important;
}

.indigo-button:visited {
    color: #FFFFFF !important;
}

.indigo-button:active {
    color: #FFFFFF !important;
}
</style>

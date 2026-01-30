from concurrent_modular_agent import AgentInterface, Agent
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path

# FastAPI module
def api_server(agent: AgentInterface):
    app = FastAPI()

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )

    # Static files directory
    dist_dir = Path(__file__).parent / "dist"

    @app.get("/")
    def root():
        agent.log("Serving index.html")
        return FileResponse(dist_dir / "index.html")

    @app.get("/ping")
    def ping():
        agent.log("Ping endpoint accessed")
        return {"status": "ok"}

    @app.get("/modules")
    def get_modules():
        agent.log("Get modules endpoint accessed")
        # Mock data - list of available modules
        modules = [
            "conversation",
            "vision",
            "soil_sensor",
            "llm_action",
            "object_avoidance",
            "inner_speech",
            "conversation_prompter"
        ]
        return {"modules": modules}

    # Mount static files (for app.js and other assets)
    app.mount("/", StaticFiles(directory=dist_dir), name="static")

    # Run FastAPI server
    agent.log("Starting FastAPI server on http://0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)

# Create agent and add module
agent = Agent('gateway_agent')
agent.add_module("api_server", api_server)
agent.start(detach=False)

import click


@click.group()
def cli():
    """CLI tool for concurrent modular agent"""
    pass


"""
Run commands
"""
from ..agent_runner import start_agent

@cli.command()
@click.argument('project_dir')
def run(project_dir):
    """Run the agent with the specified project directory"""
    start_agent(project_dir)


"""
Backend commands
"""
from .. import backend as cma_backend

@cli.group()
def backend():
    """Backend management commands"""
    pass

@backend.command()
def start():
    """Start the backend service"""
    cma_backend.start()

@backend.command()
def stop():
    """Stop the backend service"""
    cma_backend.stop()

@backend.command()
def restart():
    """Restart the backend service"""
    cma_backend.stop()
    cma_backend.start()


"""
Memory commands
"""    
from ..state import StateClient

@cli.group()
def memory():
    """Memory management commands"""
    pass

@memory.command()
def ls():
    """List memory names"""
    memory_list = StateClient.get_all_names()
    for memory in memory_list:
        print(memory)

@memory.command()
@click.argument('name')
def rm(name):
    """Delete memory with the specified name"""
    try:
        StateClient.delete_by_name(name)
        print(f"Memory '{name}' deleted successfully.")
    except ValueError as e:
        print(e)
        
@memory.command()
@click.argument('memory_name')
@click.argument('file_path')
def backup(memory_name, file_path):
    """Backup memory to the specified file path"""
    try:
        state = StateClient(memory_name)  # Ensure the memory exists
        state.backup(file_path)
        print(f"Memory backed up to '{file_path}' successfully.")
    except ValueError as e:
        print(e)

def main():
    cli()

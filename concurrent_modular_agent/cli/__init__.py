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
from ..state import MemoryManager
import os

@cli.group()
@click.option(
    "-d", "--directory",
    default=None,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="Specify memory directory which includes chroma.sqlite3",
)
@click.pass_context
def memory(ctx, directory):
    """Memory management commands"""
    ctx.obj = MemoryManager(directory)

@memory.command()
@click.pass_obj
def ls(memory_manager: MemoryManager):
    memory_list = memory_manager.get_all_names()
    for m in memory_list:
        click.echo(m)

@memory.command()
@click.pass_obj
@click.argument('agent_name')
def show(memory_manager: MemoryManager, agent_name: str):
    """Show details of memory with the specified name"""
    try:
        state_client = memory_manager.get_state_client(agent_name)
        states = state_client.get()
        click.echo(f"Memory details for '{agent_name}':")
        for state in states:
            click.echo(f"Timestamp: {state.timestamp}, ID: {state.id}, Text: {state.text}")
    except ValueError as e:
        print(e)

@memory.command()
@click.pass_obj
@click.argument('agent_name')
def rm(memory_manager: MemoryManager, agent_name: str):
    """Delete memory with the specified name"""
    try:
        if click.confirm(f"Are you sure you want to delete memory '{agent_name}'?"):
            memory_manager.delete_by_name(agent_name)
            print(f"Memory '{agent_name}' deleted successfully.")
    except ValueError as e:
        print(e)
        
@memory.command()
@click.pass_obj
@click.argument('agent_name')
@click.argument('file_path')
def dump(memory_manager: MemoryManager, agent_name: str, file_path: str):
    """Dump memory to the specified file path"""
    try:
        memory_manager.get_state_client(agent_name).dump(file_path)
        print(f"Memory dumped to '{file_path}' successfully.")
    except ValueError as e:
        print(e)

def main():
    cli()

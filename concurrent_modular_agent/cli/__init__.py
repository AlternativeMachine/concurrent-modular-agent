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
    click.echo("Warning: This command is experimental and not fully tested.")
    start_agent(project_dir)

from .memory import memory
from .backend import backend
cli.add_command(memory)
cli.add_command(backend)

def main():
    cli()

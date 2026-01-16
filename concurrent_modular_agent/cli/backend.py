import click
from .. import backend as cma_backend

@click.group()
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


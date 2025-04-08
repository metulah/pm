"""Base CLI functionality and utilities."""

from .guideline.main import guideline
from .welcome import welcome
# Import the project group from its new location
from .project.main import project
import click  # Keep click import
from .task.main import task  # Import the task group from its new location
from .note.main import note  # Import the note group from its new location
# Import the template group from its new location
from .template.main import template
from .init import init  # Import the init command


# Utility functions moved to pm/cli/common_utils.py


@click.group()
@click.option('--db-path', type=click.Path(dir_okay=False, writable=True),
              help='Path to the SQLite database file.')
@click.option('--format', type=click.Choice(['json', 'text']), default='text',
              help='Output format.')  # Add format option
@click.pass_context
def cli(ctx, db_path, format):  # Add format to signature
    """Project management CLI for AI assistants."""
    # Store the db_path in the context object for other commands to access
    ctx.ensure_object(dict)
    ctx.obj['DB_PATH'] = db_path
    ctx.obj['FORMAT'] = format  # Store format in context


# Register commands from other modules
cli.add_command(welcome)
cli.add_command(guideline)  # Register the guideline command group
cli.add_command(project)    # Register the project command group
cli.add_command(task)       # Register the task command group
cli.add_command(note)       # Register the note command group
cli.add_command(template)   # Register the template command group
cli.add_command(init)       # Register the init command

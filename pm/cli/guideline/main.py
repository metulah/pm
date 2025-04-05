# pm/cli/guideline.py
import click

# Import subcommand functions from the new files within the 'guideline' subdirectory
from .list import list_guidelines
from .show import show_guideline
from .create import create_guideline
from .update import update_guideline
from .delete import delete_guideline
from .copy import copy_guideline

# Define the guideline command group


@click.group()
@click.pass_context
def guideline(ctx):
    """Commands for managing and viewing guidelines."""
    ctx.ensure_object(dict)
    pass


# Register the imported subcommands with the guideline group
# The function object is passed, and the 'name' parameter specifies the command name in the CLI
guideline.add_command(list_guidelines, name='list')
guideline.add_command(show_guideline, name='show')
guideline.add_command(create_guideline, name='create')
guideline.add_command(update_guideline, name='update')
guideline.add_command(delete_guideline, name='delete')
guideline.add_command(copy_guideline, name='copy')

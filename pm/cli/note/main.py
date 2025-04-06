# pm/cli/note/main.py
import click

# Import subcommand functions
from .add import note_add
from .list import note_list
from .show import note_show
from .update import note_update
from .delete import note_delete


@click.group()
def note():
    """Manage notes."""
    pass


# Register subcommands
note.add_command(note_add, name='add')
note.add_command(note_list, name='list')
note.add_command(note_show, name='show')
note.add_command(note_update, name='update')
note.add_command(note_delete, name='delete')

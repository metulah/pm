# pm/cli/task/subtask/main.py
import click

# Import subcommand functions
from .create import subtask_create
from .list import subtask_list
from .show import subtask_show
from .update import subtask_update
from .delete import subtask_delete


@click.group()
def subtask():
    """Manage subtasks for tasks."""
    pass


# Register subcommands
subtask.add_command(subtask_create, name='create')
subtask.add_command(subtask_list, name='list')
subtask.add_command(subtask_show, name='show')
subtask.add_command(subtask_update, name='update')
subtask.add_command(subtask_delete, name='delete')

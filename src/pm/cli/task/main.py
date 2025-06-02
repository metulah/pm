# pm/cli/task/main.py
import click

# Import subcommand functions
from .create import task_create
from .list import task_list
from .show import task_show
from .update import task_update
from .delete import task_delete
# Import subgroups
from .dependency import dependency
from .metadata.main import metadata  # Import metadata group
from .subtask.main import subtask  # Import subtask group


@click.group()
def task():
    """Manage tasks."""
    pass


# Register direct subcommands
task.add_command(task_create, name='create')
task.add_command(task_list, name='list')
task.add_command(task_show, name='show')
task.add_command(task_update, name='update')
task.add_command(task_delete, name='delete')

# Register subgroups
task.add_command(dependency)
task.add_command(metadata)  # Register metadata group
task.add_command(subtask)  # Register subtask group

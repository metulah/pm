# pm/cli/project/main.py
import click

# Import subcommand functions
from .create import project_create
from .list import project_list
from .show import project_show
from .update import project_update
from .delete import project_delete
from .tasks import project_tasks


@click.group()
def project():
    """Manage projects."""
    pass


# Register subcommands
project.add_command(project_create, name='create')
project.add_command(project_list, name='list')
project.add_command(project_show, name='show')
project.add_command(project_update, name='update')
project.add_command(project_delete, name='delete')
project.add_command(project_tasks, name='tasks')

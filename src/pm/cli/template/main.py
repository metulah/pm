# pm/cli/template/main.py
import click

# Import subcommand functions
from .create import template_create
from .list import template_list
from .show import template_show
from .add_subtask import template_add_subtask
from .apply import template_apply
from .delete import template_delete


@click.group()
def template():
    """Manage task templates."""
    pass


# Register subcommands
template.add_command(template_create, name='create')
template.add_command(template_list, name='list')
template.add_command(template_show, name='show')
template.add_command(template_add_subtask, name='add-subtask')
template.add_command(template_apply, name='apply')
template.add_command(template_delete, name='delete')

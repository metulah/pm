# pm/cli/task/metadata/main.py
import click

# Import subcommand functions
from .set import metadata_set
from .get import metadata_get
from .delete import metadata_delete
from .query import metadata_query


@click.group()
def metadata():
    """Manage task metadata."""
    pass


# Register subcommands
metadata.add_command(metadata_set, name='set')
metadata.add_command(metadata_get, name='get')
metadata.add_command(metadata_delete, name='delete')
metadata.add_command(metadata_query, name='query')

"""Command-line interface for the PM tool."""

from .base import cli, get_db_connection, json_response
from .project import project
from .task import task
from .note import note
from .metadata import metadata
from .subtask import subtask
from .template import template

__all__ = [
    'cli',
    'get_db_connection',
    'json_response',
    'project',
    'task',
    'note',
    'metadata',
    'subtask',
    'template'
]

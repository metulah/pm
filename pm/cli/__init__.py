"""Command-line interface for the PM tool."""

from .base import cli  # Import only cli from base
# Import utilities from the new common_utils module
from .common_utils import get_db_connection, format_output
# Removed incorrect import of project group
# Removed incorrect import of task group
# Removed incorrect import of note group
# Removed incorrect import of metadata group
# Removed incorrect import of subtask group (it's part of task group now)
# Removed incorrect import of template group

__all__ = [
    'cli',
    'get_db_connection',
    'format_output',  # Export format_output
    # Removed group exports as they are registered in base.py
]

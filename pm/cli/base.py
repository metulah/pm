"""Base CLI functionality and utilities."""

import json
import click
from typing import Any, Optional

from ..storage import init_db


def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = init_db()
    return conn


def json_response(status: str, data: Optional[Any] = None, message: Optional[str] = None) -> str:
    """Create a standardized JSON response."""
    response = {"status": status}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return json.dumps(response, indent=2, default=str)


@click.group()
def cli():
    """Project management CLI for AI assistants."""
    pass

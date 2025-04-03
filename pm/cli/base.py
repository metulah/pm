"""Base CLI functionality and utilities."""

import json
import sqlite3  # Add missing import
import click
from typing import Any, Optional

from ..storage import init_db


def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database, respecting context."""
    ctx = click.get_current_context(silent=True)
    db_path = ctx.obj.get('DB_PATH') if ctx and ctx.obj else None
    # If db_path is not set in context, init_db will use its default "pm.db"
    conn = init_db(db_path) if db_path else init_db()
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
@click.option('--db-path', type=click.Path(dir_okay=False, writable=True),
              help='Path to the SQLite database file.')
@click.pass_context
def cli(ctx, db_path):
    """Project management CLI for AI assistants."""
    # Store the db_path in the context object for other commands to access
    ctx.ensure_object(dict)
    ctx.obj['DB_PATH'] = db_path

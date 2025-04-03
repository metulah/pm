"""Base CLI functionality and utilities."""

import json
import sqlite3
import click
from typing import Any, Optional, List, Dict

from ..storage import init_db


def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database, respecting context."""
    ctx = click.get_current_context(silent=True)
    db_path = ctx.obj.get('DB_PATH') if ctx and ctx.obj else None
    # If db_path is not set in context, init_db will use its default "pm.db"
    conn = init_db(db_path) if db_path else init_db()
    return conn

# --- Text Formatting Helpers ---


def _format_list_as_text(data: List[Dict[str, Any]]) -> str:
    """Formats a list of dictionaries (representing objects) as a text table."""
    if not data:
        return "No items found."

    # Determine headers from the keys of the first item
    headers = list(data[0].keys())

    # Calculate column widths (max length of header or data in that column)
    col_widths = {header: len(header) for header in headers}
    for row in data:
        for header in headers:
            col_widths[header] = max(
                col_widths[header], len(str(row.get(header, ''))))

    # Create format strings for header and rows
    header_fmt = "   ".join(f"{{:<{col_widths[h]}}}" for h in headers)
    row_fmt = "   ".join(f"{{:<{col_widths[h]}}}" for h in headers)
    separator = "   ".join("-" * col_widths[h] for h in headers)

    # Build the output string
    output = [header_fmt.format(*[h.upper() for h in headers])]
    output.append(separator)
    for row in data:
        output.append(row_fmt.format(*[str(row.get(h, '')) for h in headers]))

    return "\n".join(output)


def _format_dict_as_text(data: Dict[str, Any]) -> str:
    """Formats a dictionary (representing a single object) as key-value pairs."""
    if not data:
        return "No data found."

    # Generate labels and find the maximum length for alignment
    labels = {key: key.replace('_', ' ').title() + ':' for key in data.keys()}
    max_label_len = max(len(label)
                        for label in labels.values()) if labels else 0

    output = []
    for key, value in data.items():
        label_with_colon = labels[key]
        # Pad based on the longest label+colon length, add one space after
        output.append(f"{label_with_colon:<{max_label_len}} {value}")

    return "\n".join(output)

# --- Main Output Function ---


def format_output(format: str, status: str, data: Optional[Any] = None, message: Optional[str] = None) -> str:
    """Create a standardized response in the specified format (json or text)."""

    # Prepare data for JSON (convert objects to dicts)
    # This processing is needed for both JSON and the text formatters
    processed_data = None
    if data is not None:
        if hasattr(data, '__dict__'):
            processed_data = data.__dict__
        elif isinstance(data, list) and data and hasattr(data[0], '__dict__'):
            processed_data = [item.__dict__ for item in data]
        else:
            processed_data = data  # Assume already serializable if not object/list of objects

    if format == 'json':
        response = {"status": status}
        if processed_data is not None:
            response["data"] = processed_data
        if message is not None:
            response["message"] = message
        # Use default=str to handle potential non-serializable types like datetime
        return json.dumps(response, indent=2, default=str)

    elif format == 'text':
        if status == 'success':
            if message:
                # Simple success message (e.g., delete, update)
                return f"Success: {message}"
            elif processed_data is not None:
                # Format data based on whether it's a list or single item (dict)
                if isinstance(processed_data, list):
                    return _format_list_as_text(processed_data)
                elif isinstance(processed_data, dict):
                    return _format_dict_as_text(processed_data)
                else:
                    # Fallback for unexpected data types
                    return str(processed_data)
            else:
                # Generic success if no message or data
                return "Success!"
        else:  # status == 'error'
            # Simple error message
            return f"Error: {message}" if message else "An unknown error occurred."
    else:
        # Should not happen with click.Choice, but good practice
        return f"Error: Unsupported format '{format}'"


@click.group()
@click.option('--db-path', type=click.Path(dir_okay=False, writable=True),
              help='Path to the SQLite database file.')
@click.option('--format', type=click.Choice(['json', 'text']), default='json',
              help='Output format.')  # Add format option
@click.pass_context
def cli(ctx, db_path, format):  # Add format to signature
    """Project management CLI for AI assistants."""
    # Store the db_path in the context object for other commands to access
    ctx.ensure_object(dict)
    ctx.obj['DB_PATH'] = db_path
    ctx.obj['FORMAT'] = format  # Store format in context

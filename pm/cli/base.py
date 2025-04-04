"""Base CLI functionality and utilities."""

import json
import sqlite3
import enum
import datetime
import click
import textwrap
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
    """Formats a list of dictionaries (representing objects) as a text table with wrapping."""
    if not data:
        return "No items found."

    headers = list(data[0].keys())
    # Define max widths for specific columns that tend to be long
    MAX_WIDTHS = {'name': 40, 'description': 60}
    # Define minimum widths to prevent excessive squashing
    MIN_WIDTHS = {'id': 36, 'project_id': 36, 'task_id': 36, 'template_id': 36}

    # Calculate initial widths based on headers
    col_widths = {h: len(h) for h in headers}

    # Calculate max content width for each column, respecting MAX/MIN_WIDTHS
    for row in data:
        for h in headers:
            content_len = len(str(row.get(h, '')))
            max_w = MAX_WIDTHS.get(h.lower())
            # Default min width if not specified
            min_w = MIN_WIDTHS.get(h.lower(), 5)
            current_max = col_widths[h]

            # Determine the effective width based on content, respecting max/min constraints
            effective_content_width = content_len
            if max_w:
                effective_content_width = min(effective_content_width, max_w)

            # Final width is the max of header length, min width, and effective content width
            col_widths[h] = max(current_max, min_w, effective_content_width)

    # Create header and separator lines using final calculated widths
    header_line = "   ".join(f"{h.upper():<{col_widths[h]}}" for h in headers)
    separator_line = "   ".join("-" * col_widths[h] for h in headers)

    output_lines = [header_line, separator_line]

    # Process and format each row with wrapping
    for row in data:
        wrapped_row_lines = []
        max_lines_in_row = 1
        cell_lines_dict = {}  # Store wrapped lines for each cell in the current row

        # Wrap necessary columns and find max number of lines needed for this row
        for h in headers:
            content = str(row.get(h, ''))
            width = col_widths[h]
            # Wrap if content exceeds width OR if a max width was defined (to enforce it)
            if len(content) > width or h.lower() in MAX_WIDTHS:
                # Use textwrap.fill for simpler handling, join lines later if needed
                # Or use textwrap.wrap if multi-line cell output is desired
                wrapped_lines = textwrap.wrap(
                    content, width=width, break_long_words=False, replace_whitespace=False) if content else ['']
                cell_lines_dict[h] = wrapped_lines
                max_lines_in_row = max(max_lines_in_row, len(wrapped_lines))
            else:
                # Ensure it's treated as a list of one line for consistency
                cell_lines_dict[h] = [content]

        # Construct the output lines for the current row
        for i in range(max_lines_in_row):
            line_parts = []
            for h in headers:
                lines_for_cell = cell_lines_dict[h]
                # Get the i-th line for the cell, or empty string if it doesn't exist
                line_part = lines_for_cell[i] if i < len(
                    lines_for_cell) else ""
                line_parts.append(f"{line_part:<{col_widths[h]}}")
            output_lines.append("   ".join(line_parts))

    return "\n".join(output_lines)


def _format_dict_as_text(data: Dict[str, Any]) -> str:
    """Formats a dictionary (representing a single object) as key-value pairs."""
    if not data:
        return "No data found."

    # Calculate labels and max length first
    temp_labels = [key.replace('_', ' ').title() + ':' for key in data.keys()]
    max_label_len = max(len(label)
                        for label in temp_labels) if temp_labels else 0

    output = []
    for key, value in data.items():
        # Regenerate the label for the current key
        label_with_colon = key.replace('_', ' ').title() + ':'
        # Pad based on the calculated max length
        output.append(f"{label_with_colon:<{max_label_len}} {value}")

    return "\n".join(output)

# --- Main Output Function ---


def format_output(format: str, status: str, data: Optional[Any] = None, message: Optional[str] = None) -> str:
    """Create a standardized response in the specified format (json or text)."""

    # Prepare data for JSON/Text (convert objects/enums/datetimes to serializable types)
    processed_data = None
    if data is not None:
        items_to_process = []
        is_list = isinstance(data, list)

        if is_list:
            items_to_process = data
        else:
            items_to_process = [data]  # Treat single item as a list of one

        processed_list = []
        for item in items_to_process:
            if hasattr(item, '__dict__'):
                # Convert object to dict and process specific types
                item_dict = item.__dict__.copy()  # Work on a copy
                for key, value in item_dict.items():
                    if isinstance(value, enum.Enum):
                        item_dict[key] = value.value
                    elif isinstance(value, datetime.datetime):
                        item_dict[key] = value.isoformat()
                    # Assume other types are handled by json.dumps or are simple
                processed_list.append(item_dict)
            else:
                # If item is not an object (e.g., a dict from metadata get), pass through
                # We assume basic types like str, int, float, bool, None are fine
                processed_list.append(item)

        # Assign back to processed_data, maintaining original structure (list or single item)
        if is_list:
            processed_data = processed_list
        elif processed_list:  # Single item was processed
            processed_data = processed_list[0]
        # Input data was not a list and not processable (e.g., None, simple type)
        else:
            processed_data = data

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
                    # Pass the processed dict (enums already converted)
                    return _format_dict_as_text(processed_data)
                else:
                    # Fallback for unexpected data types (already processed)
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

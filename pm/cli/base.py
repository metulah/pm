"""Base CLI functionality and utilities."""

import json
import sqlite3
import enum
import datetime
import click
import textwrap
import uuid  # For UUID validation
import os
import io
from typing import Any, Optional, List, Dict

from ..storage import init_db
from ..storage.project import get_project, get_project_by_slug
from ..storage.task import get_task, get_task_by_slug
from ..models import Project, Task
from .welcome import welcome  # Add import for the welcome command


def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database, respecting context."""
    ctx = click.get_current_context(silent=True)
    db_path = ctx.obj.get('DB_PATH') if ctx and ctx.obj else None
    # If db_path is not set in context, init_db will use its default "pm.db"
    conn = init_db(db_path) if db_path else init_db()
    return conn
# --- Identifier Resolution Helpers ---


def _format_relative_time(dt_input: Any) -> str:
    """Formats a datetime object or ISO string into a relative time string."""
    if isinstance(dt_input, str):
        try:
            dt = datetime.datetime.fromisoformat(
                dt_input.replace('Z', '+00:00'))  # Handle Z for UTC
        except ValueError:
            return dt_input  # Return original string if parsing fails
    elif isinstance(dt_input, datetime.datetime):
        dt = dt_input
    else:
        return str(dt_input)  # Return string representation for other types

    # Ensure 'now' is timezone-aware if 'dt' is, otherwise use naive
    if dt.tzinfo:
        now = datetime.datetime.now(dt.tzinfo)
    else:
        # If dt is naive, compare with naive now.
        # Consider potential issues if naive dt represents UTC but now() is local.
        # A robust solution might involve assuming UTC for naive or converting based on context.
        now = datetime.datetime.now()

    try:
        # Add timezone awareness to naive datetime objects before subtraction if possible
        # This is a complex topic; assuming consistency for now.
        # If one is aware and the other naive, subtraction will raise TypeError.
        diff = now - dt
    except TypeError:
        # Fallback for timezone mismatch (aware vs naive)
        return dt.isoformat() + " (Timezone Mismatch)"

    seconds = diff.total_seconds()

    if seconds < 0:
        # Handle future dates gracefully
        return f"in the future ({dt.strftime('%Y-%m-%d %H:%M')})"
    elif seconds < 2:
        return "just now"
    elif seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 120:
        return "a minute ago"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minutes ago"
    elif seconds < 7200:
        return "an hour ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hours ago"
    elif seconds < 172800:  # Approx 48 hours
        return "Yesterday"  # Capitalized
    elif seconds < 2592000:  # Approx 30 days
        days = int(seconds / 86400)
        return f"{days} days ago"
    elif seconds < 5184000:  # Approx 60 days
        return "last month"
    elif seconds < 31536000:  # Approx 365 days
        # Use round for better month approximation
        months = round(seconds / 2592000)
        if months <= 1:
            return "last month"
        else:
            return f"{months} months ago"
    elif seconds < 63072000:  # Approx 2 years
        return "last year"
    else:
        years = int(seconds / 31536000)
        return f"{years} years ago"


def is_valid_uuid(identifier: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(identifier, version=4)
        return True
    except ValueError:
        return False


def resolve_project_identifier(conn: sqlite3.Connection, identifier: str) -> Project:
    """Resolve a project identifier (UUID or slug) to a Project object."""
    project = None
    if is_valid_uuid(identifier):
        project = get_project(conn, identifier)

    if project is None:
        project = get_project_by_slug(conn, identifier)

    if project is None:
        raise click.UsageError(
            f"Project not found with identifier: '{identifier}'")
    return project


def resolve_task_identifier(conn: sqlite3.Connection, project: Project, task_identifier: str) -> Task:
    """Resolve a task identifier (UUID or slug) within a given project to a Task object."""
    task = None
    if is_valid_uuid(task_identifier):
        task = get_task(conn, task_identifier)
        # Verify the found task actually belongs to the specified project
        if task and task.project_id != project.id:
            task = None  # Treat as not found if it's in the wrong project

    if task is None:
        task = get_task_by_slug(conn, project.id, task_identifier)

    if task is None:
        raise click.UsageError(
            f"Task not found with identifier '{task_identifier}' in project '{project.name}' (ID: {project.id})")
    return task


# --- Argument Processing Helpers ---


def read_content_from_argument(ctx: click.Context, param: click.Parameter, value: Optional[str]) -> Optional[str]:
    """
    Click callback to read argument content from a file if prefixed with '@'.
    Handles file reading errors and returns original value if not prefixed.
    """
    if value and value.startswith('@'):
        filepath = value[1:]
        if not filepath:
            raise click.UsageError(
                f"File path cannot be empty when using '@' prefix for option '{param.name}'.")

        # Try to resolve relative paths based on CWD
        # Note: Consider security implications if paths could be malicious
        abs_filepath = os.path.abspath(filepath)

        try:
            with io.open(abs_filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise click.UsageError(
                f"File not found for option '{param.name}': {filepath} (Resolved: {abs_filepath})")
        except PermissionError:
            raise click.UsageError(
                f"Permission denied for option '{param.name}': {filepath} (Resolved: {abs_filepath})")
        except IsADirectoryError:
            raise click.UsageError(
                f"Path is a directory, not a file, for option '{param.name}': {filepath} (Resolved: {abs_filepath})")
        except UnicodeDecodeError as e:
            raise click.UsageError(
                f"Error decoding file for option '{param.name}' (expected UTF-8): {filepath} (Resolved: {abs_filepath}) - {e}")
        except Exception as e:
            # Catch other potential OS errors during file access
            raise click.UsageError(
                f"Could not read file for option '{param.name}': {filepath} (Resolved: {abs_filepath}) - {e}")
    else:
        # Return the original value if it doesn't start with '@' or is None
        return value

# --- Text Formatting Helpers ---


# Add data_type parameter
def _format_list_as_text(data: List[Dict[str, Any]], data_type: Optional[str] = None) -> str:
    """Formats a list of dictionaries (representing objects) as a text table with wrapping, respecting context flags."""
    if not data:
        return "No items found."

    # Define preferred column orders - adjust as needed for other types (slug before name)
    # Define preferred column orders - status after description, project_slug for tasks
    PREFERRED_ORDERS = {
        'project': ['id', 'slug', 'name', 'description', 'status', 'created_at', 'updated_at'],
        # Status should be after description
        # project_slug after description, status after project_slug
        # project_slug first
        'task': ['project_slug', 'id', 'slug', 'name', 'description', 'status', 'created_at', 'updated_at'],
        # Status not typical for notes
        'note': ['id', 'project_id', 'task_id', 'content', 'created_at', 'updated_at'],
        # Added slug assumption, status after desc
        'subtask': ['id', 'slug', 'name', 'task_id', 'parent_subtask_id', 'description', 'status', 'created_at', 'updated_at'],
        # No status for templates
        'template': ['id', 'name', 'template_type', 'content', 'created_at', 'updated_at']
        # Add more types if needed
    }

    # Get context to check for flags like SHOW_ID
    ctx = click.get_current_context(silent=True)
    # Default flags to False if context or flag isn't available
    show_id = ctx.obj.get('SHOW_ID', False) if ctx and ctx.obj else False
    show_description = ctx.obj.get(
        'SHOW_DESCRIPTION', False) if ctx and ctx.obj else False
    # Type detection is now done in format_output and passed in

    # Get the actual keys present in the data (using the first item as representative)
    actual_keys = list(data[0].keys())

    if data_type and data_type in PREFERRED_ORDERS:
        preferred_order = PREFERRED_ORDERS[data_type]
        # Start with preferred order, filtering for keys present in the actual data
        potential_headers = [h for h in preferred_order if h in actual_keys]
        # Add any remaining actual keys that weren't in the preferred order (sorted for consistency)
        potential_headers.extend(
            sorted([h for h in actual_keys if h not in potential_headers]))
    else:
        # Fallback to using the actual keys if type unknown
        potential_headers = actual_keys
        # Alternatively, sort for consistency: potential_headers = sorted(actual_keys)

    # Filter headers based on context flags (e.g., show_id)
    headers = []
    for h in potential_headers:
        # Conditionally skip columns based on flags
        if h == 'id' and not show_id:
            continue
        if h == 'description' and not show_description:
            continue
        headers.append(h)

    # If headers list ended up empty (e.g., only ID was present and show_id=False), handle gracefully
    if not headers:
        return "No columns to display based on current flags."

    # Define max widths for specific columns that tend to be long
    MAX_WIDTHS = {'name': 40, 'description': 60}
    # Define minimum widths to prevent excessive squashing
    MIN_WIDTHS = {'id': 36, 'project_id': 36, 'project_slug': 20,
                  'task_id': 36, 'template_id': 36}  # Added project_slug min width

    # Calculate initial widths based on the final `headers` list
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
                    elif isinstance(value, datetime.datetime) or (isinstance(value, str) and key in ('created_at', 'updated_at')):
                        # Process datetimes or potential datetime strings for specific keys
                        if format == 'text' and key in ('created_at', 'updated_at'):
                            # Pass the original value (datetime or string) to the helper
                            item_dict[key] = _format_relative_time(value)
                        elif isinstance(value, datetime.datetime):
                            # Keep ISO format for JSON or other date fields in text
                            item_dict[key] = value.isoformat()
                        else:
                            # If it was a string but not for relative time formatting, keep it as is
                            item_dict[key] = value
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
                    # --- Start Type Detection (Moved Here) ---
                    data_type = None
                    if processed_data:  # Check if list is not empty
                        keys_sample = set(processed_data[0].keys())
                        # Heuristics for type detection - might need refinement based on actual models
                        # Note: project_id should have been removed from task data by now if text format
                        if 'project_slug' not in keys_sample and 'slug' in keys_sample and 'status' in keys_sample and 'description' in keys_sample:
                            data_type = 'project'
                        # Adjusted task detection to look for project_slug and other characteristic task keys
                        elif 'project_slug' in keys_sample and 'slug' in keys_sample and 'status' in keys_sample and 'description' in keys_sample:
                            data_type = 'task'
                        elif 'content' in keys_sample and ('task_id' in keys_sample or 'project_id' in keys_sample):
                            data_type = 'note'  # Assuming project_id might still exist if note is directly on project
                        elif 'task_id' in keys_sample and 'parent_subtask_id' in keys_sample:
                            data_type = 'subtask'
                        elif 'template_type' in keys_sample:
                            data_type = 'template'
                    # --- End Type Detection ---
                    # Pass detected type
                    return _format_list_as_text(processed_data, data_type=data_type)
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
@click.option('--format', type=click.Choice(['json', 'text']), default='text',
              help='Output format.')  # Add format option
@click.pass_context
def cli(ctx, db_path, format):  # Add format to signature
    """Project management CLI for AI assistants."""
    # Store the db_path in the context object for other commands to access
    ctx.ensure_object(dict)
    ctx.obj['DB_PATH'] = db_path
    ctx.obj['FORMAT'] = format  # Store format in context


# Register commands from other modules
cli.add_command(welcome)

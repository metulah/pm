# pm/cli/common_utils.py
"""Common utility functions shared across CLI command modules."""

import json
import sqlite3
import enum
import datetime
import click
import textwrap
import uuid
import os
import io
from typing import Any, Optional, List, Dict

# Import necessary models and storage functions used by utilities
from ..models import Project, Task
from ..storage.task import get_task, get_task_by_slug
from ..storage.project import get_project, get_project_by_slug
from ..storage import init_db

# find_project_root has been moved to pm.core.utils
# Import it from the core layer where needed
from pm.core.utils import find_project_root


def get_db_connection() -> sqlite3.Connection:
    """
    Get a connection to the SQLite database.
    Prioritizes explicit DB path from context (e.g., --db-path),
    otherwise searches upwards for the .pm directory.
    Raises ClickException if connection fails or project root not found.
    """
    # Prioritize explicit path from context (e.g., --db-path global option)
    ctx = click.get_current_context(silent=True)
    explicit_db_path = ctx.obj.get("DB_PATH") if ctx and ctx.obj else None

    if explicit_db_path:
        try:
            # Use the explicitly provided path
            conn = init_db(explicit_db_path)
            return conn
        except sqlite3.OperationalError as e:
            # Handle errors even with explicit path
            raise click.ClickException(
                f"Error connecting to specified database at '{explicit_db_path}': {e}"
            )
    else:
        # If no explicit path, search upwards for the project root
        project_root = find_project_root()
        if project_root:
            db_path = os.path.join(project_root, ".pm", "pm.db")
            try:
                conn = init_db(db_path)
                return conn
            except sqlite3.OperationalError as e:
                # Catch potential errors during connection even if path seems valid
                raise click.ClickException(
                    f"Error connecting to database at '{db_path}': {e}"
                )
        else:
            # This 'else' corresponds to 'if project_root:' (when upward search fails)
            raise click.ClickException(
                "Not inside a pm project directory (or any parent directory). "
                "Run 'pm init' to initialize a project first."
            )


def _format_relative_time(dt_input: Any) -> str:
    """Formats a datetime object or ISO string into a relative time string."""
    if isinstance(dt_input, str):
        try:
            dt = datetime.datetime.fromisoformat(
                dt_input.replace("Z", "+00:00")
            )  # Handle Z for UTC
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
        raise click.UsageError(f"Project not found with identifier: '{identifier}'")
    return project


def resolve_task_identifier(
    conn: sqlite3.Connection, project: Project, task_identifier: str
) -> Task:
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
            f"Task not found with identifier '{task_identifier}' in project '{project.name}' (ID: {project.id})"
        )
    return task


def read_content_from_argument(
    ctx: click.Context, param: click.Parameter, value: Optional[str]
) -> Optional[str]:
    """
    Click callback to read argument content from a file if prefixed with '@'.
    Handles file reading errors and returns original value if not prefixed.
    """
    if value and value.startswith("@"):
        filepath = value[1:]
        if not filepath:
            raise click.UsageError(
                f"File path cannot be empty when using '@' prefix for option '{param.name}'."
            )

        # Try to resolve relative paths based on CWD
        # Note: Consider security implications if paths could be malicious
        abs_filepath = os.path.abspath(filepath)

        try:
            with io.open(abs_filepath, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise click.UsageError(
                f"File not found for option '{param.name}': {filepath} (Resolved: {abs_filepath})"
            )
        except PermissionError:
            raise click.UsageError(
                f"Permission denied for option '{param.name}': {filepath} (Resolved: {abs_filepath})"
            )
        except IsADirectoryError:
            raise click.UsageError(
                f"Path is a directory, not a file, for option '{param.name}': {filepath} (Resolved: {abs_filepath})"
            )
        except UnicodeDecodeError as e:
            raise click.UsageError(
                f"Error decoding file for option '{param.name}' (expected UTF-8): {filepath} (Resolved: {abs_filepath}) - {e}"
            )
        except Exception as e:
            # Catch other potential OS errors during file access
            raise click.UsageError(
                f"Could not read file for option '{param.name}': {filepath} (Resolved: {abs_filepath}) - {e}"
            )
    else:
        # Return the original value if it doesn't start with '@' or is None
        return value


def _format_list_as_text(
    data: List[Dict[str, Any]], data_type: Optional[str] = None
) -> str:
    """Formats a list of dictionaries (representing objects) as a text table with wrapping, respecting context flags."""
    if not data:
        return "No items found."

    # Define preferred column orders - adjust as needed for other types (slug before name)
    # Define preferred column orders - status after description, project_slug for tasks
    PREFERRED_ORDERS = {
        "project": [
            "id",
            "slug",
            "name",
            "description",
            "status",
            "created_at",
            "updated_at",
        ],
        # Status should be after description
        # project_slug after description, status after project_slug
        # project_slug first
        "task": [
            "project_slug",
            "id",
            "slug",
            "name",
            "description",
            "status",
            "created_at",
            "updated_at",
        ],
        # Status not typical for notes
        "note": ["id", "project_id", "task_id", "content", "created_at", "updated_at"],
        # Added slug assumption, status after desc
        "subtask": [
            "id",
            "slug",
            "name",
            "task_id",
            "parent_subtask_id",
            "description",
            "status",
            "created_at",
            "updated_at",
        ],
        # No status for templates
        "template": [
            "id",
            "name",
            "template_type",
            "content",
            "created_at",
            "updated_at",
        ],
        # Add more types if needed
    }

    # Get context to check for flags like SHOW_ID
    ctx = click.get_current_context(silent=True)
    # Default flags to False if context or flag isn't available
    show_id = ctx.obj.get("SHOW_ID", False) if ctx and ctx.obj else False
    show_description = (
        ctx.obj.get("SHOW_DESCRIPTION", False) if ctx and ctx.obj else False
    )
    # Type detection is now done in format_output and passed in

    # Get the actual keys present in the data (using the first item as representative)
    actual_keys = list(data[0].keys())

    if data_type and data_type in PREFERRED_ORDERS:
        preferred_order = PREFERRED_ORDERS[data_type]
        # Start with preferred order, filtering for keys present in the actual data
        potential_headers = [h for h in preferred_order if h in actual_keys]
        # Add any remaining actual keys that weren't in the preferred order (sorted for consistency)
        potential_headers.extend(
            sorted([h for h in actual_keys if h not in potential_headers])
        )
    else:
        # Fallback to using the actual keys if type unknown
        potential_headers = actual_keys
        # Alternatively, sort for consistency: potential_headers = sorted(actual_keys)

    # Filter headers based on context flags (e.g., show_id)
    headers = []
    for h in potential_headers:
        # Conditionally skip columns based on flags
        if h == "id" and not show_id:
            continue
        if h == "description" and not show_description:
            continue
        headers.append(h)

    # If headers list ended up empty (e.g., only ID was present and show_id=False), handle gracefully
    if not headers:
        return "No columns to display based on current flags."

    # Define max widths for specific columns that tend to be long
    MAX_WIDTHS = {"name": 40, "description": 60}
    # Define minimum widths to prevent excessive squashing
    MIN_WIDTHS = {
        "id": 36,
        "project_id": 36,
        "project_slug": 20,
        "task_id": 36,
        "template_id": 36,
    }  # Added project_slug min width

    # Calculate initial widths based on the final `headers` list
    col_widths = {h: len(h) for h in headers}

    # Calculate max content width for each column, respecting MAX/MIN_WIDTHS
    for row in data:
        for h in headers:
            content_len = len(str(row.get(h, "")))
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
        max_lines_in_row = 1
        cell_lines_dict = {}  # Store wrapped lines for each cell in the current row

        # Wrap necessary columns and find max number of lines needed for this row
        for h in headers:
            content = str(row.get(h, ""))
            width = col_widths[h]
            # Wrap if content exceeds width OR if a max width was defined (to enforce it)
            if len(content) > width or h.lower() in MAX_WIDTHS:
                # Use textwrap.fill for simpler handling, join lines later if needed
                # Or use textwrap.wrap if multi-line cell output is desired
                wrapped_lines = (
                    textwrap.wrap(
                        content,
                        width=width,
                        break_long_words=False,
                        replace_whitespace=False,
                    )
                    if content
                    else [""]
                )
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
                line_part = lines_for_cell[i] if i < len(lines_for_cell) else ""
                line_parts.append(f"{line_part:<{col_widths[h]}}")
            output_lines.append("   ".join(line_parts))

    return "\n".join(output_lines)


def _format_dict_as_text(data: Dict[str, Any]) -> str:
    """Formats a dictionary (representing a single object) as key-value pairs."""
    if not data:
        return "No data found."

    # Define preferred order for single object display
    # Define preferred order for single object display, excluding 'content' for special handling
    preferred_order = [
        "id",
        "slug",
        "name",
        "project_id",
        "project_slug",
        "task_id",
        "parent_subtask_id",
        "description",
        "status",
        "note_count",
        "author",
        "entity_type",
        "entity_id",
        "created_at",
        "updated_at",
    ]

    # Extract content if present, and remove it from the data dict for separate handling
    content_to_display = data.pop("content", None)

    # Filter keys based on preferred order and what's actually in the data
    display_keys = [key for key in preferred_order if key in data]
    # Add any remaining keys from data not in preferred_order (sorted for consistency)
    display_keys.extend(sorted([key for key in data if key not in display_keys]))

    # Calculate labels and max length based on the keys we will display
    temp_labels = [key.replace("_", " ").title() + ":" for key in display_keys]
    max_label_len = max(len(label) for label in temp_labels) if temp_labels else 0

    output = []
    for key in display_keys:  # Iterate using the ordered display_keys
        value = data[key]
        # Regenerate the label for the current key
        label_with_colon = key.replace("_", " ").title() + ":"
        # Pad based on the calculated max length
        output.append(f"{label_with_colon:<{max_label_len}} {value}")

    # Append content as a separate paragraph if it exists
    if content_to_display:
        # Add a blank line before the content for separation
        output.append("")
        output.append(content_to_display)

    return "\n".join(output)


def format_output(
    format: str, status: str, data: Optional[Any] = None, message: Optional[str] = None
) -> str:
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
            if hasattr(item, "__dict__"):
                # Convert object to dict and process specific types
                item_dict = item.__dict__.copy()  # Work on a copy
                for key, value in item_dict.items():
                    if isinstance(value, enum.Enum):
                        # Special handling for status in text format
                        if format == "text" and key == "status":
                            # Replace underscore with space and capitalize first letter
                            item_dict[key] = value.value.replace("_", " ").capitalize()
                        else:
                            # Otherwise, just use the raw value (for JSON or other enums)
                            item_dict[key] = value.value
                    elif isinstance(value, datetime.datetime) or (
                        isinstance(value, str) and key in ("created_at", "updated_at")
                    ):
                        # Process datetimes or potential datetime strings for specific keys
                        if format == "text" and key in ("created_at", "updated_at"):
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

    if format == "json":
        response = {"status": status}
        if processed_data is not None:
            response["data"] = processed_data
        if message is not None:
            response["message"] = message
        # Use default=str to handle potential non-serializable types like datetime
        return json.dumps(response, indent=2, default=str)

    elif format == "text":
        if status == "success":
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
                        if (
                            "project_slug" not in keys_sample
                            and "slug" in keys_sample
                            and "status" in keys_sample
                            and "description" in keys_sample
                        ):
                            data_type = "project"
                        # Adjusted task detection to look for project_slug and other characteristic task keys
                        elif (
                            "project_slug" in keys_sample
                            and "slug" in keys_sample
                            and "status" in keys_sample
                            and "description" in keys_sample
                        ):
                            data_type = "task"
                        elif "content" in keys_sample and (
                            "task_id" in keys_sample or "project_id" in keys_sample
                        ):
                            data_type = "note"  # Assuming project_id might still exist if note is directly on project
                        elif (
                            "task_id" in keys_sample
                            and "parent_subtask_id" in keys_sample
                        ):
                            data_type = "subtask"
                        elif "template_type" in keys_sample:
                            data_type = "template"
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

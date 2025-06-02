# pm/cli/task/metadata/set.py
import json
from datetime import datetime
from typing import Optional, Any, Tuple
import click

from ....storage import update_task_metadata
# Import common utilities
from ...common_utils import get_db_connection, format_output


# Moved convert_value here as it's used by set and query
def convert_value(value: str, value_type: Optional[str] = None) -> Tuple[Any, str]:
    """Convert a string value to the appropriate type."""
    converted_value = value
    detected_type = value_type

    if value_type == "int":
        converted_value = int(value)
    elif value_type == "float":
        converted_value = float(value)
    elif value_type == "datetime":
        converted_value = datetime.fromisoformat(value)
    elif value_type == "bool":
        converted_value = value.lower() in ("true", "yes", "1")
    elif value_type == "json":
        converted_value = json.loads(value)
    elif not value_type:
        # Auto-detect type
        try:
            converted_value = int(value)
            detected_type = "int"
        except ValueError:
            try:
                converted_value = float(value)
                detected_type = "float"
            except ValueError:
                try:
                    converted_value = datetime.fromisoformat(value)
                    detected_type = "datetime"
                except ValueError:
                    if value.lower() in ("true", "false", "yes", "no", "1", "0"):
                        converted_value = value.lower() in ("true", "yes", "1")
                        detected_type = "bool"
                    else:
                        try:
                            converted_value = json.loads(value)
                            detected_type = "json"
                        except ValueError:
                            detected_type = "string"

    return converted_value, detected_type or "string"


@click.command("set")
@click.argument("task_id")
@click.option("--key", required=True, help="Metadata key")
@click.option("--value", required=True, help="Metadata value")
@click.option("--type", "value_type", type=click.Choice(["string", "int", "float", "datetime", "bool", "json"]),
              help="Value type (auto-detected if not specified)")
@click.pass_context
def metadata_set(ctx, task_id: str, key: str, value: str, value_type: Optional[str]):
    """Set metadata for a task."""
    conn = get_db_connection()
    try:
        converted_value, detected_type = convert_value(value, value_type)
        metadata = update_task_metadata(
            conn, task_id, key, converted_value, detected_type)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if metadata:
            # For text, simple message is fine. For JSON, return the object.
            if output_format == 'text':
                click.echo(format_output(output_format, "success",
                           message=f"Metadata '{key}' set for task {task_id}"))
            else:
                # Pass object for JSON
                # Construct dict for JSON output to match test expectation
                output_data = {"task_id": metadata.task_id,
                               "key": metadata.key, "value": metadata.get_value()}
                click.echo(format_output(
                    output_format, "success", output_data))
        else:
            # This case might not be reachable if update_task_metadata raises error first
            click.echo(format_output(output_format,
                                     "error", message=f"Task {task_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

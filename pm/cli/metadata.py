"""Task metadata management commands."""

import json
from datetime import datetime
from typing import Optional, Any, Tuple
import click

from ..storage import (
    update_task_metadata, get_task_metadata,
    delete_task_metadata, query_tasks_by_metadata
)
from .base import cli, get_db_connection, format_output  # Use format_output
from .task import task


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


@task.group()
def metadata():
    """Manage task metadata."""
    pass


@metadata.command("set")
@click.argument("task_id")
@click.option("--key", required=True, help="Metadata key")
@click.option("--value", required=True, help="Metadata value")
@click.option("--type", "value_type", type=click.Choice(["string", "int", "float", "datetime", "bool", "json"]),
              help="Value type (auto-detected if not specified)")
@click.pass_context  # Need context to get format
# Add ctx
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


@metadata.command("get")
@click.argument("task_id")
@click.option("--key", help="Metadata key (optional)")
@click.pass_context  # Need context to get format
def metadata_get(ctx, task_id: str, key: Optional[str]):  # Add ctx
    """Get metadata for a task."""
    conn = get_db_connection()
    try:
        metadata_list = get_task_metadata(conn, task_id, key)
        result = [{"key": m.key, "value": m.get_value(), "type": m.value_type}
                  for m in metadata_list]
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if output_format == 'text':
            if key and result:  # Specific key requested and found
                # Just print the value for text format
                click.echo(result[0]['value'])
            elif result:  # List all metadata
                click.echo(_format_list_as_text(result))  # Use list formatter
            else:
                click.echo("No metadata found.")
        else:  # JSON format
            # Pass the list of dicts
            click.echo(format_output(output_format, "success", result))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@metadata.command("delete")
@click.argument("task_id")
@click.option("--key", required=True, help="Metadata key")
@click.pass_context  # Need context to get format
def metadata_delete(ctx, task_id: str, key: str):  # Add ctx
    """Delete metadata for a task."""
    conn = get_db_connection()
    try:
        success = delete_task_metadata(conn, task_id, key)
        if success:
            # Get format from context
            output_format = ctx.obj.get('FORMAT', 'json')
            click.echo(format_output(output_format,
                                     "success", message=f"Metadata '{key}' deleted from task {task_id}"))
        else:
            # Get format from context
            output_format = ctx.obj.get('FORMAT', 'json')
            click.echo(format_output(output_format,
                                     "error", message=f"Metadata '{key}' not found for task {task_id}"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@metadata.command("query")
@click.option("--key", required=True, help="Metadata key")
@click.option("--value", required=True, help="Metadata value")
@click.option("--type", "value_type", type=click.Choice(["string", "int", "float", "datetime", "bool", "json"]),
              help="Value type (auto-detected if not specified)")
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.pass_context  # Need context to get format
# Add ctx
def metadata_query(ctx, key: str, value: str, value_type: Optional[str], debug: bool = False):
    """Query tasks by metadata."""
    conn = get_db_connection()
    try:
        # Convert the value using our helper
        converted_value, detected_type = convert_value(value, value_type)
        tasks = query_tasks_by_metadata(
            conn, key, converted_value, detected_type)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass list of task objects
        click.echo(format_output(output_format, "success", tasks))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

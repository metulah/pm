"""Task metadata management commands."""

import json
from datetime import datetime
from typing import Optional, Any, Tuple
import click

from ..storage import (
    update_task_metadata, get_task_metadata,
    delete_task_metadata, query_tasks_by_metadata
)
from .base import cli, get_db_connection, json_response
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
def metadata_set(task_id: str, key: str, value: str, value_type: Optional[str]):
    """Set metadata for a task."""
    conn = get_db_connection()
    try:
        converted_value, detected_type = convert_value(value, value_type)
        metadata = update_task_metadata(
            conn, task_id, key, converted_value, detected_type)
        if metadata:
            click.echo(json_response("success", {
                       "task_id": metadata.task_id, "key": metadata.key, "value": metadata.get_value()}))
        else:
            click.echo(json_response(
                "error", message=f"Task {task_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@metadata.command("get")
@click.argument("task_id")
@click.option("--key", help="Metadata key (optional)")
def metadata_get(task_id: str, key: Optional[str]):
    """Get metadata for a task."""
    conn = get_db_connection()
    try:
        metadata_list = get_task_metadata(conn, task_id, key)
        result = [{"key": m.key, "value": m.get_value(), "type": m.value_type}
                  for m in metadata_list]
        click.echo(json_response("success", result))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@metadata.command("delete")
@click.argument("task_id")
@click.option("--key", required=True, help="Metadata key")
def metadata_delete(task_id: str, key: str):
    """Delete metadata for a task."""
    conn = get_db_connection()
    try:
        success = delete_task_metadata(conn, task_id, key)
        if success:
            click.echo(json_response(
                "success", message=f"Metadata '{key}' deleted from task {task_id}"))
        else:
            click.echo(json_response(
                "error", message=f"Metadata '{key}' not found for task {task_id}"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@metadata.command("query")
@click.option("--key", required=True, help="Metadata key")
@click.option("--value", required=True, help="Metadata value")
@click.option("--type", "value_type", type=click.Choice(["string", "int", "float", "datetime", "bool", "json"]),
              help="Value type (auto-detected if not specified)")
@click.option("--debug", is_flag=True, help="Enable debug output")
def metadata_query(key: str, value: str, value_type: Optional[str], debug: bool = False):
    """Query tasks by metadata."""
    conn = get_db_connection()
    try:
        # Convert the value using our helper
        converted_value, detected_type = convert_value(value, value_type)
        tasks = query_tasks_by_metadata(
            conn, key, converted_value, detected_type)
        click.echo(json_response("success", [t.__dict__ for t in tasks]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()

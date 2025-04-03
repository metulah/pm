"""Subtask management commands."""

import uuid
from typing import Optional
import click

from ..models import Subtask, TaskStatus
from ..storage import (
    create_subtask, get_subtask, update_subtask,
    delete_subtask, list_subtasks
)
from .base import cli, get_db_connection, json_response
from .task import task


@task.group()
def subtask():
    """Manage subtasks for tasks."""
    pass


@subtask.command("create")
@click.argument("task_id")
@click.option("--name", required=True, help="Subtask name")
@click.option("--description", help="Subtask description")
@click.option("--required/--optional", default=True,
              help="Whether this subtask is required for task completion")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              default=TaskStatus.NOT_STARTED.value, help="Subtask status")
def subtask_create(task_id: str, name: str, description: Optional[str],
                   required: bool, status: str):
    """Create a new subtask."""
    conn = get_db_connection()
    try:
        subtask = Subtask(
            id=str(uuid.uuid4()),
            task_id=task_id,
            name=name,
            description=description,
            required_for_completion=required,
            status=TaskStatus(status)
        )
        subtask = create_subtask(conn, subtask)
        click.echo(json_response("success", subtask.to_dict()))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@subtask.command("list")
@click.argument("task_id")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="Filter by subtask status")
def subtask_list(task_id: str, status: Optional[str]):
    """List subtasks for a task."""
    conn = get_db_connection()
    try:
        status_enum = TaskStatus(status) if status else None
        subtasks = list_subtasks(conn, task_id=task_id, status=status_enum)
        click.echo(json_response("success", [s.to_dict() for s in subtasks]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@subtask.command("show")
@click.argument("subtask_id")
def subtask_show(subtask_id: str):
    """Show subtask details."""
    conn = get_db_connection()
    try:
        subtask = get_subtask(conn, subtask_id)
        if subtask:
            click.echo(json_response("success", subtask.to_dict()))
        else:
            click.echo(json_response(
                "error", message=f"Subtask {subtask_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@subtask.command("update")
@click.argument("subtask_id")
@click.option("--name", help="New subtask name")
@click.option("--description", help="New subtask description")
@click.option("--required/--optional",
              help="Whether this subtask is required for task completion")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="New subtask status")
def subtask_update(subtask_id: str, name: Optional[str], description: Optional[str],
                   required: Optional[bool], status: Optional[str]):
    """Update a subtask."""
    conn = get_db_connection()
    try:
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if required is not None:
            kwargs["required_for_completion"] = required
        if status is not None:
            kwargs["status"] = status

        subtask = update_subtask(conn, subtask_id, **kwargs)
        if subtask:
            click.echo(json_response("success", subtask.to_dict()))
        else:
            click.echo(json_response(
                "error", message=f"Subtask {subtask_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@subtask.command("delete")
@click.argument("subtask_id")
def subtask_delete(subtask_id: str):
    """Delete a subtask."""
    conn = get_db_connection()
    try:
        success = delete_subtask(conn, subtask_id)
        if success:
            click.echo(json_response(
                "success", message=f"Subtask {subtask_id} deleted"))
        else:
            click.echo(json_response(
                "error", message=f"Subtask {subtask_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()

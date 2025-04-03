"""Subtask management commands."""

import uuid
from typing import Optional
import click

from ..models import Subtask, TaskStatus
from ..storage import (
    create_subtask, get_subtask, update_subtask,
    delete_subtask, list_subtasks
)
from .base import cli, get_db_connection, format_output  # Use format_output
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
@click.pass_context  # Need context to get format
def subtask_create(ctx, task_id: str, name: str, description: Optional[str],  # Add ctx
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
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and object
        click.echo(format_output(output_format, "success", subtask))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@subtask.command("list")
@click.argument("task_id")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="Filter by subtask status")
@click.pass_context  # Need context to get format
def subtask_list(ctx, task_id: str, status: Optional[str]):  # Add ctx
    """List subtasks for a task."""
    conn = get_db_connection()
    try:
        status_enum = TaskStatus(status) if status else None
        subtasks = list_subtasks(conn, task_id=task_id, status=status_enum)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and list of objects
        click.echo(format_output(output_format, "success", subtasks))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@subtask.command("show")
@click.argument("subtask_id")
@click.pass_context  # Need context to get format
def subtask_show(ctx, subtask_id: str):  # Add ctx
    """Show subtask details."""
    conn = get_db_connection()
    try:
        subtask = get_subtask(conn, subtask_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if subtask:
            # Pass format and object
            click.echo(format_output(output_format, "success", subtask))
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Subtask {subtask_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
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
@click.pass_context  # Need context to get format
def subtask_update(ctx, subtask_id: str, name: Optional[str], description: Optional[str],  # Add ctx
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
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if subtask:
            # Pass format and object
            click.echo(format_output(output_format, "success", subtask))
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Subtask {subtask_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@subtask.command("delete")
@click.argument("subtask_id")
@click.pass_context  # Need context to get format
def subtask_delete(ctx, subtask_id: str):  # Add ctx
    """Delete a subtask."""
    conn = get_db_connection()
    try:
        success = delete_subtask(conn, subtask_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if success:
            click.echo(format_output(output_format,
                                     "success", message=f"Subtask {subtask_id} deleted"))
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Subtask {subtask_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

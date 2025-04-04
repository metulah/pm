"""Task management commands."""

import uuid
from typing import Optional
import click

from ..models import Task, TaskStatus
from ..storage import (
    create_task, get_task, update_task, delete_task, list_tasks,
    add_task_dependency, remove_task_dependency, get_task_dependencies
)
from .base import cli, get_db_connection, format_output  # Use format_output


@cli.group()
def task():
    """Manage tasks."""
    pass


@task.command("create")
@click.option("--project", required=True, help="Project ID")
@click.option("--name", required=True, help="Task name")
@click.option("--description", help="Task description")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              default=TaskStatus.NOT_STARTED.value, help="Task status")
@click.pass_context  # Need context to get format
# Add ctx
def task_create(ctx, project: str, name: str, description: Optional[str], status: str):
    """Create a new task."""
    conn = get_db_connection()
    try:
        task = Task(
            id=str(uuid.uuid4()),
            project_id=project,
            name=name,
            description=description,
            status=TaskStatus(status)
        )
        task = create_task(conn, task)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and object
        click.echo(format_output(output_format, "success", task))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@task.command("list")
@click.option("--project", help="Filter by project ID")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="Filter by task status")
@click.pass_context  # Need context to get format
def task_list(ctx, project: Optional[str], status: Optional[str]):  # Add ctx
    """List tasks with optional filters."""
    conn = get_db_connection()
    try:
        status_enum = TaskStatus(status) if status else None
        tasks = list_tasks(conn, project_id=project, status=status_enum)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and list of objects
        click.echo(format_output(output_format, "success", tasks))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@task.command("show")
@click.argument("task_id")
@click.pass_context  # Need context to get format
def task_show(ctx, task_id: str):  # Add ctx
    """Show task details."""
    conn = get_db_connection()
    try:
        task = get_task(conn, task_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if task:
            # Pass format and object
            click.echo(format_output(output_format, "success", task))
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Task {task_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@task.command("update")
@click.argument("task_id")
@click.option("--name", help="New task name")
@click.option("--description", help="New task description")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="New task status")
# Add project option
@click.option("--project", help="Move task to a different project ID")
@click.pass_context  # Need context to get format
# Add ctx
def task_update(ctx, task_id: str, name: Optional[str], description: Optional[str], status: Optional[str], project: Optional[str]):
    """Update a task."""
    conn = get_db_connection()
    try:
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if status is not None:
            kwargs["status"] = status
        if project is not None:  # Add project_id to kwargs if provided
            kwargs["project_id"] = project

        task = update_task(conn, task_id, **kwargs)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if task:
            # Pass format and object
            click.echo(format_output(output_format, "success", task))
            # If status was explicitly updated, show reminder
            if status is not None:
                 reminder = """
Reminder: Task status updated.

**Before ending this session, please ensure:**
- Session handoff note created (pm note add ...)
- Changes committed to git
- Tests pass
- Documentation is current
(See GUIDELINES.md for details)

**When starting the next task/session:**
- Remember to set the task status to IN_PROGRESS!
"""
                click.echo(reminder, err=True)
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Task {task_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@task.command("delete")
@click.argument("task_id")
@click.pass_context  # Need context to get format
def task_delete(ctx, task_id: str):  # Add ctx
    """Delete a task."""
    conn = get_db_connection()
    try:
        success = delete_task(conn, task_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if success:
            click.echo(format_output(output_format,
                                     "success", message=f"Task {task_id} deleted"))
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Task {task_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@task.group()
def dependency():
    """Manage task dependencies."""
    pass


@dependency.command("add")
@click.argument("task_id")
@click.option("--depends-on", required=True, help="Dependency task ID")
@click.pass_context  # Need context to get format
def dependency_add(ctx, task_id: str, depends_on: str):  # Add ctx
    """Add a task dependency."""
    conn = get_db_connection()
    try:
        success = add_task_dependency(conn, task_id, depends_on)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if success:
            click.echo(format_output(output_format,
                                     "success", message=f"Dependency added: {task_id} depends on {depends_on}"))
        else:
            click.echo(format_output(output_format,
                                     "error", message="Failed to add dependency"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@dependency.command("remove")
@click.argument("task_id")
@click.option("--depends-on", required=True, help="Dependency task ID")
@click.pass_context  # Need context to get format
def dependency_remove(ctx, task_id: str, depends_on: str):  # Add ctx
    """Remove a task dependency."""
    conn = get_db_connection()
    try:
        success = remove_task_dependency(conn, task_id, depends_on)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if success:
            click.echo(format_output(output_format,
                                     "success", message=f"Dependency removed: {task_id} no longer depends on {depends_on}"))
        else:
            click.echo(format_output(output_format, "error",
                       message="Dependency not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error", message=str(e)))
    finally:
        conn.close()


@dependency.command("list")
@click.argument("task_id")
@click.pass_context  # Need context to get format
def dependency_list(ctx, task_id: str):  # Add ctx
    """List task dependencies."""
    conn = get_db_connection()
    try:
        dependencies = get_task_dependencies(conn, task_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Note: get_task_dependencies already returns Task objects
        click.echo(format_output(output_format, "success", dependencies))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

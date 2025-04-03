"""Task management commands."""

import uuid
from typing import Optional
import click

from ..models import Task, TaskStatus
from ..storage import (
    create_task, get_task, update_task, delete_task, list_tasks,
    add_task_dependency, remove_task_dependency, get_task_dependencies
)
from .base import cli, get_db_connection, json_response


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
def task_create(project: str, name: str, description: Optional[str], status: str):
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
        click.echo(json_response("success", task.__dict__))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@task.command("list")
@click.option("--project", help="Filter by project ID")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="Filter by task status")
def task_list(project: Optional[str], status: Optional[str]):
    """List tasks with optional filters."""
    conn = get_db_connection()
    try:
        status_enum = TaskStatus(status) if status else None
        tasks = list_tasks(conn, project_id=project, status=status_enum)
        click.echo(json_response("success", [t.__dict__ for t in tasks]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@task.command("show")
@click.argument("task_id")
def task_show(task_id: str):
    """Show task details."""
    conn = get_db_connection()
    try:
        task = get_task(conn, task_id)
        if task:
            click.echo(json_response("success", task.__dict__))
        else:
            click.echo(json_response(
                "error", message=f"Task {task_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
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
# Add project to signature
def task_update(task_id: str, name: Optional[str], description: Optional[str], status: Optional[str], project: Optional[str]):
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
        if task:
            click.echo(json_response("success", task.__dict__))
        else:
            click.echo(json_response(
                "error", message=f"Task {task_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@task.command("delete")
@click.argument("task_id")
def task_delete(task_id: str):
    """Delete a task."""
    conn = get_db_connection()
    try:
        success = delete_task(conn, task_id)
        if success:
            click.echo(json_response(
                "success", message=f"Task {task_id} deleted"))
        else:
            click.echo(json_response(
                "error", message=f"Task {task_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@task.group()
def dependency():
    """Manage task dependencies."""
    pass


@dependency.command("add")
@click.argument("task_id")
@click.option("--depends-on", required=True, help="Dependency task ID")
def dependency_add(task_id: str, depends_on: str):
    """Add a task dependency."""
    conn = get_db_connection()
    try:
        success = add_task_dependency(conn, task_id, depends_on)
        if success:
            click.echo(json_response(
                "success", message=f"Dependency added: {task_id} depends on {depends_on}"))
        else:
            click.echo(json_response(
                "error", message="Failed to add dependency"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@dependency.command("remove")
@click.argument("task_id")
@click.option("--depends-on", required=True, help="Dependency task ID")
def dependency_remove(task_id: str, depends_on: str):
    """Remove a task dependency."""
    conn = get_db_connection()
    try:
        success = remove_task_dependency(conn, task_id, depends_on)
        if success:
            click.echo(json_response(
                "success", message=f"Dependency removed: {task_id} no longer depends on {depends_on}"))
        else:
            click.echo(json_response("error", message="Dependency not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@dependency.command("list")
@click.argument("task_id")
def dependency_list(task_id: str):
    """List task dependencies."""
    conn = get_db_connection()
    try:
        dependencies = get_task_dependencies(conn, task_id)
        click.echo(json_response(
            "success", [d.__dict__ for d in dependencies]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()

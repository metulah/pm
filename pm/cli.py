import json
import sqlite3
import uuid
import click
from datetime import datetime
from .models import Project, Task, TaskStatus, TaskMetadata
from .storage import (
    init_db, create_project, get_project, update_project, delete_project, list_projects,
    create_task, get_task, update_task, delete_task, list_tasks,
    add_task_dependency, remove_task_dependency, get_task_dependencies,
    create_task_metadata, get_task_metadata, get_task_metadata_value,
    update_task_metadata, delete_task_metadata, query_tasks_by_metadata
)


def get_db_connection():
    """Get a connection to the SQLite database."""
    conn = init_db()
    return conn


def json_response(status: str, data=None, message=None):
    """Create a standardized JSON response."""
    response = {"status": status}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return json.dumps(response, indent=2, default=str)


@click.group()
def cli():
    """Project management CLI for AI assistants."""
    pass


@cli.group()
def project():
    """Manage projects."""
    pass


@project.command("create")
@click.option("--name", required=True, help="Project name")
@click.option("--description", help="Project description")
def project_create(name, description):
    """Create a new project."""
    conn = get_db_connection()
    try:
        project = Project(id=str(uuid.uuid4()), name=name,
                          description=description)
        project = create_project(conn, project)
        click.echo(json_response("success", project.__dict__))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@project.command("list")
def project_list():
    """List all projects."""
    conn = get_db_connection()
    try:
        projects = list_projects(conn)
        click.echo(json_response("success", [p.__dict__ for p in projects]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@project.command("show")
@click.argument("project_id")
def project_show(project_id):
    """Show project details."""
    conn = get_db_connection()
    try:
        project = get_project(conn, project_id)
        if project:
            click.echo(json_response("success", project.__dict__))
        else:
            click.echo(json_response(
                "error", message=f"Project {project_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@project.command("update")
@click.argument("project_id")
@click.option("--name", help="New project name")
@click.option("--description", help="New project description")
def project_update(project_id, name, description):
    """Update a project."""
    conn = get_db_connection()
    try:
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description

        project = update_project(conn, project_id, **kwargs)
        if project:
            click.echo(json_response("success", project.__dict__))
        else:
            click.echo(json_response(
                "error", message=f"Project {project_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@project.command("delete")
@click.argument("project_id")
def project_delete(project_id):
    """Delete a project."""
    conn = get_db_connection()
    try:
        success = delete_project(conn, project_id)
        if success:
            click.echo(json_response(
                "success", message=f"Project {project_id} deleted"))
        else:
            click.echo(json_response(
                "error", message=f"Project {project_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


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
def task_create(project, name, description, status):
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
def task_list(project, status):
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
def task_show(task_id):
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
def task_update(task_id, name, description, status):
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
def task_delete(task_id):
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
def dependency_add(task_id, depends_on):
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
def dependency_remove(task_id, depends_on):
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
def dependency_list(task_id):
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
def metadata_set(task_id, key, value, value_type):
    """Set metadata for a task."""
    conn = get_db_connection()
    try:
        # Convert value based on type
        if value_type == "int":
            value = int(value)
        elif value_type == "float":
            value = float(value)
        elif value_type == "datetime":
            value = datetime.fromisoformat(value)
        elif value_type == "bool":
            value = value.lower() in ("true", "yes", "1")
        elif value_type == "json":
            value = json.loads(value)

        metadata = update_task_metadata(conn, task_id, key, value, value_type)
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
def metadata_get(task_id, key):
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
def metadata_delete(task_id, key):
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
def metadata_query(key, value, value_type):
    """Query tasks by metadata."""
    conn = get_db_connection()
    try:
        # Convert value based on type
        if value_type == "int":
            value = int(value)
        elif value_type == "float":
            value = float(value)
        elif value_type == "datetime":
            value = datetime.fromisoformat(value)
        elif value_type == "bool":
            value = value.lower() in ("true", "yes", "1")
        elif value_type == "json":
            value = json.loads(value)

        tasks = query_tasks_by_metadata(conn, key, value, value_type)
        click.echo(json_response("success", [t.__dict__ for t in tasks]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


if __name__ == "__main__":
    cli()

import json
import sqlite3
import uuid
import click
from datetime import datetime
from .models import (
    Project, Task, TaskStatus, TaskMetadata, Note, Subtask,
    TaskTemplate, SubtaskTemplate
)
from .storage import (
    init_db, create_project, get_project, update_project, delete_project, list_projects,
    create_task, get_task, update_task, delete_task, list_tasks,
    add_task_dependency, remove_task_dependency, get_task_dependencies,
    create_task_metadata, get_task_metadata, get_task_metadata_value,
    update_task_metadata, delete_task_metadata, query_tasks_by_metadata,
    create_note, get_note, update_note, delete_note, list_notes,
    create_subtask, get_subtask, update_subtask, delete_subtask, list_subtasks,
    create_task_template, get_task_template, update_task_template, delete_task_template,
    list_task_templates, create_subtask_template, get_subtask_template,
    update_subtask_template, delete_subtask_template, list_subtask_templates,
    apply_template_to_task
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


@task.group()
def subtask():
    """Manage subtasks for tasks."""
    pass


@subtask.command("create")
@click.argument("task_id")
@click.option("--name", required=True, help="Subtask name")
@click.option("--description", help="Subtask description")
@click.option("--required/--optional", default=True, help="Whether this subtask is required for task completion")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              default=TaskStatus.NOT_STARTED.value, help="Subtask status")
def subtask_create(task_id, name, description, required, status):
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
def subtask_list(task_id, status):
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
def subtask_show(subtask_id):
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
@click.option("--required/--optional", help="Whether this subtask is required for task completion")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="New subtask status")
def subtask_update(subtask_id, name, description, required, status):
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
def subtask_delete(subtask_id):
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


@cli.group()
def template():
    """Manage task templates."""
    pass


@template.command("create")
@click.option("--name", required=True, help="Template name")
@click.option("--description", help="Template description")
def template_create(name, description):
    """Create a new task template."""
    conn = get_db_connection()
    try:
        template = TaskTemplate(
            id=str(uuid.uuid4()),
            name=name,
            description=description
        )
        template = create_task_template(conn, template)
        click.echo(json_response("success", template.to_dict()))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@template.command("list")
def template_list():
    """List all task templates."""
    conn = get_db_connection()
    try:
        templates = list_task_templates(conn)
        click.echo(json_response("success", [t.to_dict() for t in templates]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@template.command("show")
@click.argument("template_id")
def template_show(template_id):
    """Show template details."""
    conn = get_db_connection()
    try:
        template = get_task_template(conn, template_id)
        if template:
            result = template.to_dict()
            subtasks = list_subtask_templates(conn, template_id)
            result["subtasks"] = [s.to_dict() for s in subtasks]
            click.echo(json_response("success", result))
        else:
            click.echo(json_response(
                "error", message=f"Template {template_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@template.command("add-subtask")
@click.argument("template_id")
@click.option("--name", required=True, help="Subtask template name")
@click.option("--description", help="Subtask template description")
@click.option("--required/--optional", default=True, help="Whether this subtask is required for task completion")
def template_add_subtask(template_id, name, description, required):
    """Add a subtask to a template."""
    conn = get_db_connection()
    try:
        subtask = SubtaskTemplate(
            id=str(uuid.uuid4()),
            template_id=template_id,
            name=name,
            description=description,
            required_for_completion=required
        )
        subtask = create_subtask_template(conn, subtask)
        click.echo(json_response("success", subtask.to_dict()))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@template.command("apply")
@click.argument("template_id")
@click.option("--task", required=True, help="Task ID to apply template to")
def template_apply(template_id, task):
    """Apply a template to a task."""
    conn = get_db_connection()
    try:
        subtasks = apply_template_to_task(conn, task, template_id)
        click.echo(json_response("success", {
            "task_id": task,
            "template_id": template_id,
            "subtasks_created": len(subtasks),
            "subtasks": [s.to_dict() for s in subtasks]
        }))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@template.command("delete")
@click.argument("template_id")
def template_delete(template_id):
    """Delete a template."""
    conn = get_db_connection()
    try:
        success = delete_task_template(conn, template_id)
        if success:
            click.echo(json_response(
                "success", message=f"Template {template_id} deleted"))
        else:
            click.echo(json_response(
                "error", message=f"Template {template_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@cli.group()
def note():
    """Manage notes for tasks and projects."""
    pass


@note.command("add")
@click.option("--task", help="Task ID to add note to")
@click.option("--project", help="Project ID to add note to")
@click.option("--content", required=True, help="Note content")
@click.option("--author", help="Note author")
def note_add(task, project, content, author):
    """Add a note to a task or project."""
    if not task and not project:
        click.echo(json_response(
            "error", message="Must specify either --task or --project"))
        return
    if task and project:
        click.echo(json_response(
            "error", message="Cannot specify both --task and --project"))
        return

    entity_type = "task" if task else "project"
    entity_id = task if task else project

    conn = get_db_connection()
    try:
        note = Note(
            id=str(uuid.uuid4()),
            content=content,
            author=author,
            entity_type=entity_type,
            entity_id=entity_id
        )
        note = create_note(conn, note)
        click.echo(json_response("success", note.to_dict()))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@note.command("list")
@click.option("--task", help="Task ID to list notes for")
@click.option("--project", help="Project ID to list notes for")
def note_list(task, project):
    """List notes for a task or project."""
    if not task and not project:
        click.echo(json_response(
            "error", message="Must specify either --task or --project"))
        return
    if task and project:
        click.echo(json_response(
            "error", message="Cannot specify both --task and --project"))
        return

    entity_type = "task" if task else "project"
    entity_id = task if task else project

    conn = get_db_connection()
    try:
        notes = list_notes(conn, entity_type, entity_id)
        click.echo(json_response("success", [n.to_dict() for n in notes]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@note.command("show")
@click.argument("note_id")
def note_show(note_id):
    """Show note details."""
    conn = get_db_connection()
    try:
        note = get_note(conn, note_id)
        if note:
            click.echo(json_response("success", note.to_dict()))
        else:
            click.echo(json_response(
                "error", message=f"Note {note_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@note.command("update")
@click.argument("note_id")
@click.option("--content", help="New note content")
@click.option("--author", help="New note author")
def note_update(note_id, content, author):
    """Update a note."""
    conn = get_db_connection()
    try:
        kwargs = {}
        if content is not None:
            kwargs["content"] = content
        if author is not None:
            kwargs["author"] = author

        note = update_note(conn, note_id, **kwargs)
        if note:
            click.echo(json_response("success", note.to_dict()))
        else:
            click.echo(json_response(
                "error", message=f"Note {note_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@note.command("delete")
@click.argument("note_id")
def note_delete(note_id):
    """Delete a note."""
    conn = get_db_connection()
    try:
        success = delete_note(conn, note_id)
        if success:
            click.echo(json_response(
                "success", message=f"Note {note_id} deleted"))
        else:
            click.echo(json_response(
                "error", message=f"Note {note_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


if __name__ == "__main__":
    cli()

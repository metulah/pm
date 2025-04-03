"""Template management commands."""

import uuid
from typing import Optional
import click

from ..models import TaskTemplate, SubtaskTemplate
from ..storage import (
    create_task_template, get_task_template,
    update_task_template, delete_task_template,
    list_task_templates, create_subtask_template,
    get_subtask_template, update_subtask_template,
    delete_subtask_template, list_subtask_templates,
    apply_template_to_task
)
from .base import cli, get_db_connection, json_response


@cli.group()
def template():
    """Manage task templates."""
    pass


@template.command("create")
@click.option("--name", required=True, help="Template name")
@click.option("--description", help="Template description")
def template_create(name: str, description: Optional[str]):
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
def template_show(template_id: str):
    """Show template details."""
    conn = get_db_connection()
    try:
        template = get_task_template(conn, template_id)
        if template:
            # Get subtasks for this template
            subtasks = list_subtask_templates(conn, template_id)
            result = template.to_dict()
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
@click.option("--required/--optional", default=True,
              help="Whether this subtask is required for task completion")
def template_add_subtask(template_id: str, name: str, description: Optional[str],
                         required: bool):
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
def template_apply(template_id: str, task: str):
    """Apply a template to create subtasks for a task."""
    conn = get_db_connection()
    try:
        subtasks = apply_template_to_task(conn, task, template_id)
        click.echo(json_response("success", [s.to_dict() for s in subtasks]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@template.command("delete")
@click.argument("template_id")
def template_delete(template_id: str):
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

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
from .base import cli, get_db_connection, format_output  # Use format_output


@cli.group()
def template():
    """Manage task templates."""
    pass


@template.command("create")
@click.option("--name", required=True, help="Template name")
@click.option("--description", help="Template description")
@click.pass_context  # Need context to get format
def template_create(ctx, name: str, description: Optional[str]):  # Add ctx
    """Create a new task template."""
    conn = get_db_connection()
    try:
        template = TaskTemplate(
            id=str(uuid.uuid4()),
            name=name,
            description=description
        )
        template = create_task_template(conn, template)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and object
        click.echo(format_output(output_format, "success", template))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@template.command("list")
@click.pass_context  # Need context to get format
def template_list(ctx):  # Add ctx
    """List all task templates."""
    conn = get_db_connection()
    try:
        templates = list_task_templates(conn)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and list of objects
        click.echo(format_output(output_format, "success", templates))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@template.command("show")
@click.argument("template_id")
@click.pass_context  # Need context to get format
def template_show(ctx, template_id: str):  # Add ctx
    """Show template details."""
    conn = get_db_connection()
    try:
        template = get_task_template(conn, template_id)
        if template:
            # Get subtasks for this template
            subtasks = list_subtask_templates(conn, template_id)
            result = template.to_dict()
            result["subtasks"] = [s.to_dict() for s in subtasks]
            # Get format from context
            output_format = ctx.obj.get('FORMAT', 'json')
            # For text format, we might want a custom display showing template info + subtasks
            # For now, pass the combined dict; format_output handles dicts
            click.echo(format_output(output_format, "success", result))
        else:
            # Get format from context
            output_format = ctx.obj.get('FORMAT', 'json')
            click.echo(format_output(output_format,
                                     "error", message=f"Template {template_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@template.command("add-subtask")
@click.argument("template_id")
@click.option("--name", required=True, help="Subtask template name")
@click.option("--description", help="Subtask template description")
@click.option("--required/--optional", default=True,
              help="Whether this subtask is required for task completion")
@click.pass_context  # Need context to get format
def template_add_subtask(ctx, template_id: str, name: str, description: Optional[str],  # Add ctx
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


@template.command("apply")
@click.argument("template_id")
@click.option("--task", required=True, help="Task ID to apply template to")
@click.pass_context  # Need context to get format
def template_apply(ctx, template_id: str, task: str):  # Add ctx
    """Apply a template to create subtasks for a task."""
    conn = get_db_connection()
    try:
        subtasks = apply_template_to_task(conn, task, template_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass list of created subtask objects
        click.echo(format_output(output_format, "success", subtasks))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@template.command("delete")
@click.argument("template_id")
@click.pass_context  # Need context to get format
def template_delete(ctx, template_id: str):  # Add ctx
    """Delete a template."""
    conn = get_db_connection()
    try:
        success = delete_task_template(conn, template_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if success:
            click.echo(format_output(output_format,
                                     "success", message=f"Template {template_id} deleted"))
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Template {template_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

# pm/cli/template/show.py
import click

from ...storage import get_task_template, list_subtask_templates
# Import common utilities
from ..common_utils import get_db_connection, format_output


@click.command("show")
@click.argument("template_id")
@click.pass_context
def template_show(ctx, template_id: str):
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

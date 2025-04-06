# pm/cli/template/apply.py
import click

from ...storage import apply_template_to_task
# Import common utilities
from ..common_utils import get_db_connection, format_output


@click.command("apply")
@click.argument("template_id")
@click.option("--task", required=True, help="Task ID to apply template to")
@click.pass_context
def template_apply(ctx, template_id: str, task: str):
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

# pm/cli/template/delete.py
import click

from ...storage import delete_task_template
# Import common utilities
from ..common_utils import get_db_connection, format_output


@click.command("delete")
@click.argument("template_id")
@click.pass_context
def template_delete(ctx, template_id: str):
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

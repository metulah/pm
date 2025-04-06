# pm/cli/template/list.py
import click

from ...storage import list_task_templates
# Import common utilities
from ..common_utils import get_db_connection, format_output


@click.command("list")
@click.pass_context
def template_list(ctx):
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

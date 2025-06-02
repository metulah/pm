# pm/cli/template/add_subtask.py
import uuid
from typing import Optional
import click

from ...models import SubtaskTemplate
from ...storage import create_subtask_template
# Import common utilities
from ..common_utils import get_db_connection, format_output


@click.command("add-subtask")
@click.argument("template_id")
@click.option("--name", required=True, help="Subtask template name")
@click.option("--description", help="Subtask template description")
@click.option("--required/--optional", default=True,
              help="Whether this subtask is required for task completion")
@click.pass_context
def template_add_subtask(ctx, template_id: str, name: str, description: Optional[str],
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

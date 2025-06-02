# pm/cli/template/create.py
import uuid
from typing import Optional
import click

from ...models import TaskTemplate
from ...storage import create_task_template
# Import common utilities
from ..common_utils import get_db_connection, format_output


@click.command("create")
@click.option("--name", required=True, help="Template name")
@click.option("--description", help="Template description")
@click.pass_context
def template_create(ctx, name: str, description: Optional[str]):
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

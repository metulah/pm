# pm/cli/task/metadata/delete.py
import click

from ....storage import delete_task_metadata
# Import common utilities
from ...common_utils import get_db_connection, format_output


@click.command("delete")
@click.argument("task_id")
@click.option("--key", required=True, help="Metadata key")
@click.pass_context
def metadata_delete(ctx, task_id: str, key: str):
    """Delete metadata for a task."""
    conn = get_db_connection()
    try:
        success = delete_task_metadata(conn, task_id, key)
        if success:
            # Get format from context
            output_format = ctx.obj.get('FORMAT', 'json')
            click.echo(format_output(output_format,
                                     "success", message=f"Metadata '{key}' deleted from task {task_id}"))
        else:
            # Get format from context
            output_format = ctx.obj.get('FORMAT', 'json')
            click.echo(format_output(output_format,
                                     "error", message=f"Metadata '{key}' not found for task {task_id}"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

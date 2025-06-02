# pm/cli/task/metadata/get.py
from typing import Optional
import click

from ....storage import get_task_metadata
# Import common utilities
from ...common_utils import get_db_connection, format_output, _format_list_as_text


@click.command("get")
@click.argument("task_id")
@click.option("--key", help="Metadata key (optional)")
@click.pass_context
def metadata_get(ctx, task_id: str, key: Optional[str]):
    """Get metadata for a task."""
    conn = get_db_connection()
    try:
        metadata_list = get_task_metadata(conn, task_id, key)
        result = [{"key": m.key, "value": m.get_value(), "type": m.value_type}
                  for m in metadata_list]
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if output_format == 'text':
            if key and result:  # Specific key requested and found
                # Just print the value for text format
                click.echo(result[0]['value'])
            elif result:  # List all metadata
                # Pass data_type='metadata' or similar if specific formatting needed
                click.echo(_format_list_as_text(result))
            else:
                click.echo("No metadata found.")
        else:  # JSON format
            # Pass the list of dicts
            click.echo(format_output(output_format, "success", result))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

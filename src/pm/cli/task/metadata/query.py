# pm/cli/task/metadata/query.py
from typing import Optional
import click

from ....storage import query_tasks_by_metadata
# Import common utilities
from ...common_utils import get_db_connection, format_output
# Import convert_value from the sibling 'set' module
from .set import convert_value


@click.command("query")
@click.option("--key", required=True, help="Metadata key")
@click.option("--value", required=True, help="Metadata value")
@click.option("--type", "value_type", type=click.Choice(["string", "int", "float", "datetime", "bool", "json"]),
              help="Value type (auto-detected if not specified)")
# Keep debug flag if needed, though not used in current code
@click.option("--debug", is_flag=True, help="Enable debug output")
@click.pass_context
def metadata_query(ctx, key: str, value: str, value_type: Optional[str], debug: bool = False):
    """Query tasks by metadata."""
    conn = get_db_connection()
    try:
        # Convert the value using our helper
        converted_value, detected_type = convert_value(value, value_type)
        tasks = query_tasks_by_metadata(
            conn, key, converted_value, detected_type)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass list of task objects
        click.echo(format_output(output_format, "success", tasks))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

# pm/cli/note/delete.py
import click

from ...storage import delete_note
# Import common utilities
from ..common_utils import get_db_connection, format_output


@click.command("delete")
@click.argument("note_id")
@click.pass_context
def note_delete(ctx, note_id: str):
    """Delete a note."""
    conn = get_db_connection()
    try:
        success = delete_note(conn, note_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if success:
            click.echo(format_output(output_format,
                                     "success", message=f"Note {note_id} deleted"))
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Note {note_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error", message=str(e)))
    finally:
        conn.close()

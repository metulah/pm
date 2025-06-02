# pm/cli/note/show.py
import click

from ...storage import get_note
# Import common utilities
from ..common_utils import get_db_connection, format_output


@click.command("show")
@click.argument("note_id")
@click.pass_context
def note_show(ctx, note_id: str):
    """Show note details."""
    conn = get_db_connection()
    try:
        note = get_note(conn, note_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if note:
            # Pass format and object
            click.echo(format_output(output_format, "success", note))
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Note {note_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error", message=str(e)))
    finally:
        conn.close()

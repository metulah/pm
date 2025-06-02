# pm/cli/note/update.py
from typing import Optional
import click

from ...storage import update_note
# Import common utilities
from ..common_utils import get_db_connection, format_output


@click.command("update")
@click.argument("note_id")
@click.option("--content", required=True, help="New note content")
@click.option("--author", help="New note author")
@click.pass_context
def note_update(ctx, note_id: str, content: str, author: Optional[str]):
    """Update a note."""
    conn = get_db_connection()
    try:
        kwargs = {"content": content}
        if author is not None:
            kwargs["author"] = author

        note = update_note(conn, note_id, **kwargs)
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

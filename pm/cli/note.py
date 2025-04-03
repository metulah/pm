"""Note management commands."""

import uuid
from typing import Optional
import click

from ..models import Note
from ..storage import (
    create_note, get_note, update_note,
    delete_note, list_notes
)
from .base import cli, get_db_connection, format_output  # Use format_output


@cli.group()
def note():
    """Manage notes."""
    pass


@note.command("add")
@click.option("--task", help="Task ID")
@click.option("--project", help="Project ID")
@click.option("--content", required=True, help="Note content")
@click.option("--author", help="Note author")
@click.pass_context  # Need context to get format
def note_add(ctx, task: Optional[str], project: Optional[str], content: str, author: Optional[str]):  # Add ctx
    """Add a new note."""
    if not task and not project:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message="Either --task or --project must be specified"))
        return
    if task and project:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message="Cannot specify both --task and --project"))
        return

    conn = get_db_connection()
    try:
        note = Note(
            id=str(uuid.uuid4()),
            content=content,
            entity_type="task" if task else "project",
            entity_id=task or project,
            author=author
        )
        note = create_note(conn, note)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and object
        click.echo(format_output(output_format, "success", note))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@note.command("list")
@click.option("--task", help="Task ID")
@click.option("--project", help="Project ID")
@click.pass_context  # Need context to get format
def note_list(ctx, task: Optional[str], project: Optional[str]):  # Add ctx
    """List notes for a task or project."""
    if not task and not project:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message="Either --task or --project must be specified"))
        return
    if task and project:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message="Cannot specify both --task and --project"))
        return

    conn = get_db_connection()
    try:
        entity_type = "task" if task else "project"
        entity_id = task or project
        notes = list_notes(conn, entity_type=entity_type, entity_id=entity_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and list of objects
        click.echo(format_output(output_format, "success", notes))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@note.command("show")
@click.argument("note_id")
@click.pass_context  # Need context to get format
def note_show(ctx, note_id: str):  # Add ctx
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
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@note.command("update")
@click.argument("note_id")
@click.option("--content", required=True, help="New note content")
@click.option("--author", help="New note author")
@click.pass_context  # Need context to get format
# Add ctx
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
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@note.command("delete")
@click.argument("note_id")
@click.pass_context  # Need context to get format
def note_delete(ctx, note_id: str):  # Add ctx
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
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

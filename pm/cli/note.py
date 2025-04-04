"""Note management commands."""

import uuid
from typing import Optional
import click

from ..models import Note
from ..storage import (
    create_note, get_note, update_note,
    delete_note, list_notes
)
# Import resolvers
from .base import cli, get_db_connection, format_output, resolve_project_identifier, resolve_task_identifier


@cli.group()
def note():
    """Manage notes."""
    pass


@note.command("add")
@click.option("--project", 'project_identifier', help="Target Project identifier (ID or slug). Required.")
@click.option("--task", 'task_identifier', help="Target Task identifier (ID or slug). If provided, note is attached to the task within the specified project.")
@click.option("--content", required=True, help="Note content")
@click.option("--author", help="Note author")
@click.pass_context
def note_add(ctx, project_identifier: Optional[str], task_identifier: Optional[str], content: str, author: Optional[str]):
    """Add a new note to a project or a task within a project."""
    output_format = ctx.obj.get('FORMAT', 'json')

    # Validation: --project is always required now if we target a task via slug
    if not project_identifier:
        click.echo(format_output(output_format, "error",
                   message="--project must be specified."))
        return
    # Note: We don't need to explicitly check for only --task, as click handles required --project

    conn = get_db_connection()
    try:
        entity_type = None
        entity_id = None

        # Always resolve project first
        project_obj = resolve_project_identifier(conn, project_identifier)

        if task_identifier:
            # Target is a task within the specified project
            task_obj = resolve_task_identifier(
                conn, project_obj, task_identifier)
            entity_type = "task"
            entity_id = task_obj.id
        else:
            # Target is the project itself
            entity_type = "project"
            entity_id = project_obj.id

        # Create and save the note
        note_data = Note(
            id=str(uuid.uuid4()),
            content=content,
            entity_type=entity_type,
            entity_id=entity_id,  # Use the resolved ID
            author=author
        )
        note = create_note(conn, note_data)

        # Output result
        click.echo(format_output(output_format, "success", note))
    except Exception as e:
        # Handle errors
        click.echo(format_output(output_format, "error", message=str(e)))
    finally:
        conn.close()


@note.command("list")
@click.option("--project", 'project_identifier', help="List notes for this Project (ID or slug). Required.")
@click.option("--task", 'task_identifier', help="List notes for this Task (ID or slug) within the specified project.")
@click.pass_context
def note_list(ctx, project_identifier: Optional[str], task_identifier: Optional[str]):
    """List notes for a project or a specific task within a project."""
    output_format = ctx.obj.get('FORMAT', 'json')

    # Validation: --project is always required
    if not project_identifier:
        click.echo(format_output(output_format, "error",
                   message="--project must be specified."))
        return

    conn = get_db_connection()
    try:
        entity_type = None
        entity_id = None

        # Always resolve project first
        project_obj = resolve_project_identifier(conn, project_identifier)

        if task_identifier:
            # Target is a task within the specified project
            task_obj = resolve_task_identifier(
                conn, project_obj, task_identifier)
            entity_type = "task"
            entity_id = task_obj.id
        else:
            # Target is the project itself
            entity_type = "project"
            entity_id = project_obj.id

        notes = list_notes(conn, entity_type=entity_type, entity_id=entity_id)
        # Pass format and list of objects
        click.echo(format_output(output_format, "success", notes))
    except Exception as e:
        # Get format from context
        click.echo(format_output(output_format, "error", message=str(e)))
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
        click.echo(format_output(output_format, "error", message=str(e)))
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
        click.echo(format_output(output_format, "error", message=str(e)))
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
        click.echo(format_output(output_format, "error", message=str(e)))
    finally:
        conn.close()

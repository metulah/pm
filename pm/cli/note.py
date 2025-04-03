"""Note management commands."""

import uuid
from typing import Optional
import click

from ..models import Note
from ..storage import (
    create_note, get_note, update_note,
    delete_note, list_notes
)
from .base import cli, get_db_connection, json_response


@cli.group()
def note():
    """Manage notes."""
    pass


@note.command("add")
@click.option("--task", help="Task ID")
@click.option("--project", help="Project ID")
@click.option("--content", required=True, help="Note content")
@click.option("--author", help="Note author")
def note_add(task: Optional[str], project: Optional[str], content: str, author: Optional[str]):
    """Add a new note."""
    if not task and not project:
        click.echo(json_response(
            "error", message="Either --task or --project must be specified"))
        return
    if task and project:
        click.echo(json_response(
            "error", message="Cannot specify both --task and --project"))
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
        click.echo(json_response("success", note.__dict__))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@note.command("list")
@click.option("--task", help="Task ID")
@click.option("--project", help="Project ID")
def note_list(task: Optional[str], project: Optional[str]):
    """List notes for a task or project."""
    if not task and not project:
        click.echo(json_response(
            "error", message="Either --task or --project must be specified"))
        return
    if task and project:
        click.echo(json_response(
            "error", message="Cannot specify both --task and --project"))
        return

    conn = get_db_connection()
    try:
        notes = list_notes(
            conn, "task" if task else "project", task or project)
        click.echo(json_response("success", [n.__dict__ for n in notes]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@note.command("show")
@click.argument("note_id")
def note_show(note_id: str):
    """Show note details."""
    conn = get_db_connection()
    try:
        note = get_note(conn, note_id)
        if note:
            click.echo(json_response("success", note.__dict__))
        else:
            click.echo(json_response(
                "error", message=f"Note {note_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@note.command("update")
@click.argument("note_id")
@click.option("--content", required=True, help="New note content")
@click.option("--author", help="New note author")
def note_update(note_id: str, content: str, author: Optional[str]):
    """Update a note."""
    conn = get_db_connection()
    try:
        kwargs = {"content": content}
        if author is not None:
            kwargs["author"] = author

        note = update_note(conn, note_id, **kwargs)
        if note:
            click.echo(json_response("success", note.__dict__))
        else:
            click.echo(json_response(
                "error", message=f"Note {note_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@note.command("delete")
@click.argument("note_id")
def note_delete(note_id: str):
    """Delete a note."""
    conn = get_db_connection()
    try:
        success = delete_note(conn, note_id)
        if success:
            click.echo(json_response(
                "success", message=f"Note {note_id} deleted"))
        else:
            click.echo(json_response(
                "error", message=f"Note {note_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()

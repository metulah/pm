# pm/cli/note/add.py
import uuid
from typing import Optional
import click

from ...models import Note
from ...storage import create_note
# Import common utilities
from ..common_utils import get_db_connection, format_output, resolve_project_identifier, resolve_task_identifier, read_content_from_argument


@click.command("add")
@click.option("--project", 'project_identifier', help="Target Project identifier (ID or slug). Required.")
@click.option("--task", 'task_identifier', help="Target Task identifier (ID or slug). If provided, note is attached to the task within the specified project.")
@click.option("--content", required=True, help="Note content (or @filepath to read from file).", callback=read_content_from_argument)
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

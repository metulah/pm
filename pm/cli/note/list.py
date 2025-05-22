# pm/cli/note/list.py
from typing import Optional
import click

from ...storage import list_notes

# Import common utilities
from ..common_utils import (
    get_db_connection,
    format_output,
    resolve_project_identifier,
    resolve_task_identifier,
)


@click.command("list")
@click.option(
    "--project",
    "project_identifier",
    help="List notes for this Project (ID or slug). Required.",
)
@click.option(
    "--task",
    "task_identifier",
    help="List notes for this Task (ID or slug) within the specified project.",
)
@click.pass_context
def note_list(ctx, project_identifier: Optional[str], task_identifier: Optional[str]):
    """List notes for a project or a specific task within a project."""
    output_format = ctx.obj.get("FORMAT", "json")

    # Validation: --project is always required
    if not project_identifier:
        click.echo(
            format_output(
                output_format, "error", message="--project must be specified."
            )
        )
        return

    conn = get_db_connection()
    try:
        entity_type = None
        entity_id = None

        # Always resolve project first
        project_obj = resolve_project_identifier(conn, project_identifier)

        if task_identifier:
            # Target is a task within the specified project
            task_obj = resolve_task_identifier(conn, project_obj, task_identifier)
            entity_type = "task"
            entity_id = task_obj.id
        else:
            # Target is the project itself
            entity_type = "project"
            entity_id = project_obj.id

        notes = list_notes(conn, entity_type=entity_type, entity_id=entity_id)
        if not notes:
            click.echo(
                format_output(output_format, "success", message="No notes found.")
            )
            return

        # For text format, print each note individually for better readability
        if output_format == "text":
            for i, note in enumerate(notes):
                if i > 0:
                    click.echo("\n" + "=" * 40 + "\n")  # Separator between notes
                click.echo(format_output(output_format, "success", note))
        else:
            # For JSON or other formats, pass the list of objects
            click.echo(format_output(output_format, "success", notes))
    except Exception as e:
        # Get format from context
        click.echo(format_output(output_format, "error", message=str(e)))
    finally:
        conn.close()

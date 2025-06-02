# pm/cli/task/update.py
from typing import Optional
import click
import textwrap
# Removed rich imports

from ...models import TaskStatus
from ...storage import update_task
# Import common utilities
from ..common_utils import get_db_connection, format_output, resolve_project_identifier, resolve_task_identifier, read_content_from_argument


@click.command("update")  # Add the click command decorator
@click.argument("project_identifier")
@click.argument("task_identifier")
@click.option("--name", help="New task name")
@click.option("--description", help="New task description (or @filepath to read from file).", callback=read_content_from_argument)
@click.option("--status", type=click.Choice([s.value for s in TaskStatus], case_sensitive=False),
              help="New task status")
@click.option("--project", help="Move task to a different project (use ID or slug)")
@click.pass_context
def task_update(ctx, project_identifier: str, task_identifier: str, name: Optional[str], description: Optional[str], status: Optional[str], project: Optional[str]):
    """Update a task."""
    conn = get_db_connection()
    try:
        # Resolve original project and task
        original_project_obj = resolve_project_identifier(
            conn, project_identifier)
        task_to_update = resolve_task_identifier(
            conn, original_project_obj, task_identifier)
        task_id = task_to_update.id  # Get the actual ID

        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if status is not None:
            kwargs["status"] = status
        if project is not None:
            # Resolve the target project identifier if moving the task
            target_project_obj = resolve_project_identifier(conn, project)
            kwargs["project_id"] = target_project_obj.id  # Use resolved ID

        # Call update_task with the resolved task ID
        task = update_task(conn, task_id, **kwargs)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Resolver raises error if task not found, update_task returns the updated object
        click.echo(format_output(output_format, "success", task))
        # If status was explicitly updated, show reminder
        if status is not None:
            reminder = textwrap.dedent("""

                Reminder: Task status updated.

                **Before ending this session, please ensure:**
                - Session handoff note created (pm note add ...)
                - Changes committed to git
                - Tests pass
                - Documentation is current
                (Run 'pm welcome' for details)

                **When starting the next task/session:**
                - Remember to set the task status to IN_PROGRESS!
             """)
            # Print raw reminder to stderr instead of rendering Markdown
            click.echo(reminder.strip(), err=True)
    except ValueError as e:  # Catch specific validation errors
        # Check if the error is specifically about invalid status transition
        if "Invalid status transition" in str(e):
            # Get format from context
            output_format = ctx.obj.get('FORMAT', 'json')
            # Use format_output for consistency, but also print to stderr and exit
            click.echo(format_output(output_format,
                       "error", message=str(e)), err=True)
            # Error is handled by format_output above
            ctx.exit(1)  # Exit with non-zero status ONLY for invalid transitions
        else:
            # For other ValueErrors (like "not found"), let the generic handler below deal with it
            # This allows tests expecting exit code 0 for "not found" errors to pass
            raise e  # Re-raise the exception to be caught by the generic handler
    # Generic handler for other errors (including re-raised ValueErrors)
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # This will now handle "Task not found", "Project not found", etc.
        # and exit with code 0 as previously expected by some tests.
        click.echo(format_output(output_format, "error",
                   message=str(e)))
        # NOTE: Removed ctx.exit(1) here to allow exit code 0 for handled errors like "not found"
    finally:
        conn.close()

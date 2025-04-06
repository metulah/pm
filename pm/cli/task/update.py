# pm/cli/task/update.py
from typing import Optional
import click
import textwrap
from rich.console import Console
from rich.markdown import Markdown

from ...models import TaskStatus
from ...storage import update_task
# Import common utilities
from ..common_utils import get_db_connection, format_output, resolve_project_identifier, resolve_task_identifier, read_content_from_argument


@click.command("update")  # Add the click command decorator
@click.argument("project_identifier")
@click.argument("task_identifier")
@click.option("--name", help="New task name")
@click.option("--description", help="New task description (or @filepath to read from file).", callback=read_content_from_argument)
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
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
            console = Console(stderr=True)
            console.print(Markdown(reminder.strip()))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

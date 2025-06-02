# pm/cli/project/update.py
from typing import Optional
import click
import textwrap

from ...storage import update_project
from ...core.types import ProjectStatus
from ..common_utils import get_db_connection, format_output, resolve_project_identifier, read_content_from_argument


@click.command("update")  # Add the click command decorator
@click.argument("identifier")
@click.option("--name", help="New project name")
@click.option("--description", help="New project description (or @filepath to read from file).", callback=read_content_from_argument)
@click.option("--status", type=click.Choice([s.value for s in ProjectStatus], case_sensitive=False),
              help="New project status (ACTIVE, PROSPECTIVE, COMPLETED, ARCHIVED, CANCELLED)")
@click.pass_context
def project_update(ctx, identifier: str, name: Optional[str], description: Optional[str], status: Optional[str]):
    """Update a project."""
    conn = get_db_connection()
    try:
        # Resolve identifier first to get the project ID
        project_to_update = resolve_project_identifier(conn, identifier)
        project_id = project_to_update.id

        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if status is not None:
            kwargs["status"] = status

        # Call update_project with the resolved ID
        project = update_project(conn, project_id, **kwargs)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # update_project returns the updated project object (or None if ID was invalid, though resolver should prevent this)
        # Resolver raises error if not found, so we assume project exists here
        click.echo(format_output(output_format, "success", project))
        # If status was explicitly updated, show reminder
        if status is not None:
            reminder = textwrap.dedent("""

               Reminder: Project status updated. Consider the following:
               - Ensure all related tasks are appropriately status'd (e.g., COMPLETED).
               - Update overall project documentation/notes if needed.
               - Consider archiving related artifacts if project is COMPLETED/ARCHIVED.
            """)
            click.echo(reminder, err=True)
    except ValueError as e:  # Catch specific validation errors
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)  # Exit with non-zero status
    except Exception as e:  # Keep generic handler for other errors
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

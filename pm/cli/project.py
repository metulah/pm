"""Project management commands."""

import uuid
from typing import Optional
import click
import textwrap  # Import textwrap

from ..models import Project
# Removed sys import again if present
from ..storage import (
    create_project, get_project, update_project,
    delete_project, list_projects, ProjectNotEmptyError
)
from ..core.types import ProjectStatus  # Import ProjectStatus
# Import resolver
from .base import cli, get_db_connection, format_output, resolve_project_identifier


@cli.group()
def project():
    """Manage projects."""
    pass


@project.command("create")
@click.option("--name", required=True, help="Project name")
@click.option("--description", help="Project description")
@click.option("--status", type=click.Choice([s.value for s in ProjectStatus]),  # Updated choices
              default=ProjectStatus.ACTIVE.value, help="Initial project status (ACTIVE, COMPLETED, ARCHIVED, CANCELLED)")
@click.pass_context  # Need context to get format
# Add status to signature
def project_create(ctx, name: str, description: Optional[str], status: str):
    """Create a new project."""
    conn = get_db_connection()
    try:
        # Slug is generated by create_project, so it's not passed here
        project_data = Project(id=str(uuid.uuid4()), name=name,
                               description=description,
                               status=ProjectStatus(status))
        # create_project now returns the full object with slug
        project = create_project(conn, project_data)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and object
        click.echo(format_output(output_format, "success", project))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@project.command("list")
# Add --id flag
@click.option('--id', 'show_id', is_flag=True, default=False, help='Show the full ID column in text format.')
# Add --completed flag
@click.option('--completed', 'include_completed', is_flag=True, default=False, help='Include completed projects in the list.')
# Add --description flag
@click.option('--description', 'show_description', is_flag=True, default=False, help='Show the full description column in text format.')
# Add --archived flag
@click.option('--archived', 'include_archived', is_flag=True, default=False, help='Include archived and cancelled projects in the list.')
@click.pass_context
# Add include_archived to signature
def project_list(ctx, show_id: bool, include_completed: bool, show_description: bool, include_archived: bool):
    """List all projects."""
    conn = get_db_connection()
    try:
        # print("DEBUG[project_list]: 1 - Getting projects", file=sys.stderr) # Removed debug
        # Pass flag to storage function
        projects = list_projects(conn, include_completed=include_completed,
                                 include_archived=include_archived)  # Pass flags to storage function
        # print(f"DEBUG[project_list]: 2 - Got {len(projects)} projects", file=sys.stderr) # Removed debug
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass the show_id flag to the context for the formatter
        ctx.obj['SHOW_ID'] = show_id
        ctx.obj['SHOW_DESCRIPTION'] = show_description  # Pass flag to context
        # print(f"DEBUG[project_list]: 3 - Format is '{output_format}'", file=sys.stderr) # Removed debug
        # Pass format and list of objects
        formatted_output = format_output(output_format, "success", projects)
        # print("DEBUG[project_list]: 4 - Formatting successful", file=sys.stderr) # Removed debug
        click.echo(formatted_output)
    except Exception as e:
        # print(f"DEBUG[project_list]: 5 - Caught Exception: {repr(e)}", file=sys.stderr) # Removed debug
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # print(f"DEBUG[project_list]: 6 - Formatting error message", file=sys.stderr) # Removed debug
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@project.command("show")
@click.argument("identifier")  # Changed name from project_id to identifier
@click.pass_context
def project_show(ctx, identifier: str):
    """Show project details."""
    conn = get_db_connection()
    try:
        project = resolve_project_identifier(conn, identifier)  # Use resolver
        output_format = ctx.obj.get('FORMAT', 'json')
        # Resolver raises error if not found, so we assume project exists here
        click.echo(format_output(output_format, "success", project))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # print(f"DEBUG[project_show_except]: Caught Exception: type={type(e)}, repr='{repr(e)}', str='{str(e)}'", file=sys.stderr) # Removed debug
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@project.command("update")
@click.argument("identifier")  # Changed name from project_id to identifier
@click.option("--name", help="New project name")
@click.option("--description", help="New project description")
@click.option("--status", type=click.Choice([s.value for s in ProjectStatus]),  # Updated choices
              help="New project status (ACTIVE, COMPLETED, ARCHIVED, CANCELLED)")
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
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@project.command("delete")
@click.argument("identifier")  # Changed name from project_id to identifier
@click.option('--force', is_flag=True, default=False, help='Force delete project and all associated tasks.')
@click.pass_context
def project_delete(ctx, identifier: str, force: bool):
    """Delete a project."""
    conn = get_db_connection()
    try:
        # Resolve identifier first to get the project ID
        project_to_delete = resolve_project_identifier(conn, identifier)
        project_id = project_to_delete.id

        # Call delete_project with the resolved ID
        success = delete_project(conn, project_id, force=force)
        output_format = ctx.obj.get('FORMAT', 'json')
        # Resolver raises error if not found, delete_project returns bool based on deletion success
        # We rely on delete_project's return value and ProjectNotEmptyError
        if success:
            click.echo(format_output(output_format, "success",
                       message=f"Project '{identifier}' deleted"))
        else:
            # This case should ideally not be reached if resolver works and delete_project raises errors correctly
            click.echo(format_output(output_format, "error",
                       message=f"Failed to delete project '{identifier}'"))

    except ProjectNotEmptyError as e:  # Catch the specific error
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error", message=str(e)))
    except Exception as e:  # Keep generic error handling
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error", message=str(e)))
    finally:
        conn.close()

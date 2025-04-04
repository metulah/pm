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
from .base import cli, get_db_connection, format_output  # Use format_output


@cli.group()
def project():
    """Manage projects."""
    pass


@project.command("create")
@click.option("--name", required=True, help="Project name")
@click.option("--description", help="Project description")
@click.option("--status", type=click.Choice([s.value for s in ProjectStatus]),
              default=ProjectStatus.ACTIVE.value, help="Initial project status")  # Add status option
@click.pass_context  # Need context to get format
# Add status to signature
def project_create(ctx, name: str, description: Optional[str], status: str):
    """Create a new project."""
    conn = get_db_connection()
    try:
        project = Project(id=str(uuid.uuid4()), name=name,
                          description=description,
                          status=ProjectStatus(status))  # Set status from arg
        project = create_project(conn, project)
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
@click.pass_context  # Need context to get format
def project_list(ctx):  # Add ctx
    """List all projects."""
    conn = get_db_connection()
    try:
        # print("DEBUG[project_list]: 1 - Getting projects", file=sys.stderr) # Removed debug
        projects = list_projects(conn)
        # print(f"DEBUG[project_list]: 2 - Got {len(projects)} projects", file=sys.stderr) # Removed debug
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
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
@click.argument("project_id")
@click.pass_context  # Need context to get format
def project_show(ctx, project_id: str):  # Add ctx
    """Show project details."""
    conn = get_db_connection()
    try:
        project = get_project(conn, project_id)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if project:
            # Pass format and object
            click.echo(format_output(output_format, "success", project))
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Project {project_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # print(f"DEBUG[project_show_except]: Caught Exception: type={type(e)}, repr='{repr(e)}', str='{str(e)}'", file=sys.stderr) # Removed debug
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@project.command("update")
@click.argument("project_id")
@click.option("--name", help="New project name")
@click.option("--description", help="New project description")
@click.option("--status", type=click.Choice([s.value for s in ProjectStatus]),
              help="New project status")  # Add status option
@click.pass_context  # Need context to get format
# Add status to signature
def project_update(ctx, project_id: str, name: Optional[str], description: Optional[str], status: Optional[str]):
    """Update a project."""
    conn = get_db_connection()
    try:
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description
        if status is not None:
            kwargs["status"] = status  # Add status to kwargs

        project = update_project(conn, project_id, **kwargs)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if project:
            # Pass format and object
            click.echo(format_output(output_format, "success", project))
            # If status was explicitly updated, show reminder
            if status is not None:
                # Add leading newline for separation
                reminder = textwrap.dedent("""
                   Reminder: Project status updated. Consider the following:
                   - Ensure all related tasks are appropriately status'd (e.g., COMPLETED).
                   - Update overall project documentation/notes if needed.
                   - Consider archiving related artifacts if project is COMPLETED/ARCHIVED.
                """)  # Removed extra blank line at start
                click.echo(
                    reminder, err=True)  # Removed .strip() to keep leading newline
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Project {project_id} not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@project.command("delete")
@click.argument("project_id")
# Add force flag
@click.option('--force', is_flag=True, default=False, help='Force delete project and all associated tasks.')
@click.pass_context  # Need context to get format
def project_delete(ctx, project_id: str, force: bool):  # Add ctx
    """Delete a project."""
    conn = get_db_connection()
    try:
        # Call the modified storage function
        success = delete_project(
            conn, project_id, force=force)  # Pass force flag
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if success:
            click.echo(format_output(output_format,
                                     "success", message=f"Project {project_id} deleted"))
        else:
            # This case might be less likely now if ProjectNotEmptyError is raised first
            click.echo(format_output(output_format,
                                     "error", message=f"Project {project_id} not found"))
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

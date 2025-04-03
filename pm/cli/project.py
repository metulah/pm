"""Project management commands."""

import uuid
from typing import Optional
import click

from ..models import Project
from ..storage import (
    create_project, get_project, update_project,
    delete_project, list_projects, ProjectNotEmptyError  # Import ProjectNotEmptyError
)
from .base import cli, get_db_connection, format_output  # Use format_output


@cli.group()
def project():
    """Manage projects."""
    pass


@project.command("create")
@click.option("--name", required=True, help="Project name")
@click.option("--description", help="Project description")
@click.pass_context  # Need context to get format
def project_create(ctx, name: str, description: str):  # Add ctx
    """Create a new project."""
    conn = get_db_connection()
    try:
        project = Project(id=str(uuid.uuid4()), name=name,
                          description=description)
        project = create_project(conn, project)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and object
        click.echo(format_output(output_format, "success", project))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@project.command("list")
@click.pass_context  # Need context to get format
def project_list(ctx):  # Add ctx
    """List all projects."""
    conn = get_db_connection()
    try:
        projects = list_projects(conn)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and list of objects
        click.echo(format_output(output_format, "success", projects))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
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
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@project.command("update")
@click.argument("project_id")
@click.option("--name", help="New project name")
@click.option("--description", help="New project description")
@click.pass_context  # Need context to get format
# Add ctx
def project_update(ctx, project_id: str, name: Optional[str], description: Optional[str]):
    """Update a project."""
    conn = get_db_connection()
    try:
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description

        project = update_project(conn, project_id, **kwargs)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        if project:
            # Pass format and object
            click.echo(format_output(output_format, "success", project))
        else:
            click.echo(format_output(output_format,
                                     "error", message=f"Project {project_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
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

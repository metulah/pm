"""Project management commands."""

import uuid
from typing import Optional
import click

from ..models import Project
from ..storage import (
    create_project, get_project, update_project,
    delete_project, list_projects, ProjectNotEmptyError  # Import ProjectNotEmptyError
)
from .base import cli, get_db_connection, json_response


@cli.group()
def project():
    """Manage projects."""
    pass


@project.command("create")
@click.option("--name", required=True, help="Project name")
@click.option("--description", help="Project description")
def project_create(name: str, description: str):
    """Create a new project."""
    conn = get_db_connection()
    try:
        project = Project(id=str(uuid.uuid4()), name=name,
                          description=description)
        project = create_project(conn, project)
        click.echo(json_response("success", project.__dict__))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@project.command("list")
def project_list():
    """List all projects."""
    conn = get_db_connection()
    try:
        projects = list_projects(conn)
        click.echo(json_response("success", [p.__dict__ for p in projects]))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@project.command("show")
@click.argument("project_id")
def project_show(project_id: str):
    """Show project details."""
    conn = get_db_connection()
    try:
        project = get_project(conn, project_id)
        if project:
            click.echo(json_response("success", project.__dict__))
        else:
            click.echo(json_response(
                "error", message=f"Project {project_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@project.command("update")
@click.argument("project_id")
@click.option("--name", help="New project name")
@click.option("--description", help="New project description")
def project_update(project_id: str, name: Optional[str], description: Optional[str]):
    """Update a project."""
    conn = get_db_connection()
    try:
        kwargs = {}
        if name is not None:
            kwargs["name"] = name
        if description is not None:
            kwargs["description"] = description

        project = update_project(conn, project_id, **kwargs)
        if project:
            click.echo(json_response("success", project.__dict__))
        else:
            click.echo(json_response(
                "error", message=f"Project {project_id} not found"))
    except Exception as e:
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()


@project.command("delete")
@click.argument("project_id")
def project_delete(project_id: str):
    """Delete a project."""
    conn = get_db_connection()
    try:
        # Call the modified storage function
        success = delete_project(conn, project_id)
        if success:
            click.echo(json_response(
                "success", message=f"Project {project_id} deleted"))
        else:
            # This case might be less likely now if ProjectNotEmptyError is raised first
            click.echo(json_response(
                "error", message=f"Project {project_id} not found"))
    except ProjectNotEmptyError as e:  # Catch the specific error
        click.echo(json_response("error", message=str(e)))
    except Exception as e:  # Keep generic error handling
        click.echo(json_response("error", message=str(e)))
    finally:
        conn.close()

# pm/cli/task/dependency.py
import click

from ...storage import add_task_dependency, remove_task_dependency, get_task_dependencies
# Import common utilities
from ..common_utils import get_db_connection, format_output, resolve_project_identifier, resolve_task_identifier


@click.group()
def dependency():
    """Manage task dependencies."""
    pass


@dependency.command("add")
@click.argument("project_identifier")
@click.argument("task_identifier")
@click.option("--depends-on", required=True, help="Dependency task identifier (ID or slug)")
@click.pass_context
def dependency_add(ctx, project_identifier: str, task_identifier: str, depends_on: str):
    """Add a task dependency."""
    conn = get_db_connection()
    try:
        # Resolve project and both tasks
        project_obj = resolve_project_identifier(conn, project_identifier)
        task_obj = resolve_task_identifier(conn, project_obj, task_identifier)
        # Assume dependency is in same project
        dependency_obj = resolve_task_identifier(conn, project_obj, depends_on)

        success = add_task_dependency(
            conn, task_obj.id, dependency_obj.id)  # Use resolved IDs
        output_format = ctx.obj.get('FORMAT', 'json')
        if success:
            click.echo(format_output(output_format, "success",
                       message=f"Dependency added: Task '{task_identifier}' now depends on '{depends_on}'"))
        else:
            # This might indicate the dependency already exists or another integrity issue
            click.echo(format_output(output_format, "error",
                       message=f"Failed to add dependency from '{task_identifier}' to '{depends_on}'"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@dependency.command("remove")
@click.argument("project_identifier")
@click.argument("task_identifier")
@click.option("--depends-on", required=True, help="Dependency task identifier (ID or slug)")
@click.pass_context
def dependency_remove(ctx, project_identifier: str, task_identifier: str, depends_on: str):
    """Remove a task dependency."""
    conn = get_db_connection()
    try:
        # Resolve project and both tasks
        project_obj = resolve_project_identifier(conn, project_identifier)
        task_obj = resolve_task_identifier(conn, project_obj, task_identifier)
        # Assume dependency is in same project
        dependency_obj = resolve_task_identifier(conn, project_obj, depends_on)

        success = remove_task_dependency(
            conn, task_obj.id, dependency_obj.id)  # Use resolved IDs
        output_format = ctx.obj.get('FORMAT', 'json')
        if success:
            click.echo(format_output(output_format, "success",
                       message=f"Dependency removed: Task '{task_identifier}' no longer depends on '{depends_on}'"))
        else:
            click.echo(format_output(output_format, "error",
                       message=f"Dependency from '{task_identifier}' to '{depends_on}' not found"))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error", message=str(e)))
    finally:
        conn.close()


@dependency.command("list")
@click.argument("project_identifier")
@click.argument("task_identifier")
@click.pass_context
def dependency_list(ctx, project_identifier: str, task_identifier: str):
    """List task dependencies."""
    conn = get_db_connection()
    try:
        # Resolve project and task
        project_obj = resolve_project_identifier(conn, project_identifier)
        task_obj = resolve_task_identifier(conn, project_obj, task_identifier)

        dependencies = get_task_dependencies(
            conn, task_obj.id)  # Use resolved ID
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Note: get_task_dependencies already returns Task objects
        click.echo(format_output(output_format, "success", dependencies))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

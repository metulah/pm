# pm/cli/task/show.py
import click

from ...storage import get_task_dependencies
# Import common utilities
from ..common_utils import get_db_connection, format_output, resolve_project_identifier, resolve_task_identifier


@click.command("show")  # Add the click command decorator
@click.argument("project_identifier")
@click.argument("task_identifier")
@click.pass_context
def task_show(ctx, project_identifier: str, task_identifier: str):
    """Show task details."""
    conn = get_db_connection()
    try:
        # Resolve project first, then task within that project
        project_obj = resolve_project_identifier(conn, project_identifier)
        task = resolve_task_identifier(
            conn, project_obj, task_identifier)  # Use resolver

        # Fetch dependencies
        dependencies = get_task_dependencies(conn, task.id)
        # Get slugs for cleaner display
        dependency_slugs = [dep.slug for dep in dependencies if dep.slug]
        # Add dependencies to the task object for output formatting
        setattr(task, 'dependencies', dependency_slugs)

        output_format = ctx.obj.get('FORMAT', 'json')

        # For text format, add project_slug and remove project_id for consistency with list
        if output_format == 'text':
            setattr(task, 'project_slug', project_obj.slug)
            if hasattr(task, 'project_id'):
                delattr(task, 'project_id')

        # Resolver raises error if not found, so we assume task exists here
        # Pass the modified task object (now with dependencies and potentially project_slug)
        click.echo(format_output(output_format, "success", task))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

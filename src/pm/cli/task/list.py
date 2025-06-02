# pm/cli/task/list.py
from typing import Optional
import click

from ...models import TaskStatus
from ...storage import list_tasks, get_project
# Import common utilities
from ..common_utils import get_db_connection, format_output, resolve_project_identifier


@click.command("list")  # Add the click command decorator
@click.option("--project", help="Filter by project identifier (ID or slug)")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="Filter by task status")
@click.option('--id', 'show_id', is_flag=True, default=False, help='Show the full ID column in text format.')
@click.option('--completed', 'include_completed', is_flag=True, default=False, help='Include completed tasks in the list (unless --status is used).')
@click.option('--abandoned', 'include_abandoned', is_flag=True, default=False, help='Include abandoned tasks in the list (unless --status is used).')
@click.option('--description', 'show_description', is_flag=True, default=False, help='Show the full description column in text format.')
@click.option('--inactive', 'include_inactive_project_tasks', is_flag=True, default=False, help='Include tasks from non-ACTIVE projects.')
@click.option('--all', 'list_all', is_flag=True, default=False,
              help='List all tasks from all projects, regardless of status (overrides --project, --status, --completed, --abandoned, and implies --inactive).')
@click.pass_context
def task_list(ctx, project: Optional[str], status: Optional[str], show_id: bool, include_completed: bool, include_abandoned: bool, show_description: bool, include_inactive_project_tasks: bool, list_all: bool):
    """List tasks with optional filters."""
    conn = get_db_connection()
    try:
        project_id = None
        status_enum = TaskStatus(status) if status else None

        # Handle the --all flag: overrides project and status filters
        if list_all:
            project_id = None  # Override --project
            status_enum = None  # Override --status
            include_completed = True  # Override --completed=False
            include_abandoned = True  # Override --abandoned=False
            include_inactive_project_tasks = True  # Imply --inactive
        elif project:
            # Resolve project identifier only if --all is not specified
            project_obj = resolve_project_identifier(conn, project)
            project_id = project_obj.id
        # else: project is None and list_all is False, so project_id remains None (list all tasks from active projects by default)

        # Fetch tasks using the determined filters
        tasks = list_tasks(conn, project_id=project_id, status=status_enum,
                           include_completed=include_completed, include_abandoned=include_abandoned, include_inactive_project_tasks=include_inactive_project_tasks)

        output_format = ctx.obj.get('FORMAT', 'json')
        ctx.obj['SHOW_ID'] = show_id
        ctx.obj['SHOW_DESCRIPTION'] = show_description  # Pass flag to context

        # If text format, add project_slug attribute to each task object
        # This allows format_output to handle datetime conversion correctly
        if output_format == 'text' and tasks:
            project_cache = {}
            for task in tasks:
                project_slug = "UNKNOWN_PROJECT"  # Default value
                if task.project_id:
                    if task.project_id not in project_cache:
                        # Fetch project if not already cached
                        try:
                            project_obj = get_project(conn, task.project_id)
                            project_cache[task.project_id] = project_obj.slug if project_obj else "UNKNOWN_PROJECT"
                        except Exception:
                            project_cache[task.project_id] = "ERROR_FETCHING_PROJECT"
                    project_slug = project_cache[task.project_id]
                # Dynamically add the attribute to the object itself
                setattr(task, 'project_slug', project_slug)
                # Explicitly remove project_id if it exists, so it doesn't get added back by the formatter
                if hasattr(task, 'project_id'):
                    delattr(task, 'project_id')

        # Pass the (potentially modified) list of Task objects to the formatter
        # format_output will handle converting objects to dicts and formatting dates
        click.echo(format_output(output_format, "success", tasks))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

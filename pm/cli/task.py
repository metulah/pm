"""Task management commands."""

import uuid
from typing import Optional
import click
import textwrap  # Import textwrap

from ..models import Task, TaskStatus
from ..storage import (
    create_task, get_task, update_task, delete_task, list_tasks,
    add_task_dependency, remove_task_dependency, get_task_dependencies
)
from ..storage.project import get_project  # Import get_project (Fixed syntax)
# Import resolvers and helper
from .base import cli, get_db_connection, format_output, resolve_project_identifier, resolve_task_identifier, read_content_from_argument


@cli.group()
def task():
    """Manage tasks."""
    pass


@task.command("create")
@click.option("--project", required=True, help="Project identifier (ID or slug)")
@click.option("--name", required=True, help="Task name")
@click.option("--description", help="Task description (or @filepath to read from file).", callback=read_content_from_argument)
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              default=TaskStatus.NOT_STARTED.value, help="Task status")
@click.pass_context
def task_create(ctx, project: str, name: str, description: Optional[str], status: str):
    """Create a new task."""
    conn = get_db_connection()
    try:
        # Resolve project identifier first
        project_obj = resolve_project_identifier(conn, project)

        # Create task data object (slug is generated by create_task)
        task_data = Task(
            id=str(uuid.uuid4()),
            project_id=project_obj.id,  # Use resolved project ID
            name=name,
            description=description,
            status=TaskStatus(status)
        )
        # create_task returns full object with slug
        task = create_task(conn, task_data)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass format and object
        click.echo(format_output(output_format, "success", task))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@task.command("list")
@click.option("--project", help="Filter by project identifier (ID or slug)")
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="Filter by task status")
# Add --id flag
@click.option('--id', 'show_id', is_flag=True, default=False, help='Show the full ID column in text format.')
# Add --completed flag
@click.option('--completed', 'include_completed', is_flag=True, default=False, help='Include completed tasks in the list (unless --status is used).')
# Add --abandoned flag
@click.option('--abandoned', 'include_abandoned', is_flag=True, default=False, help='Include abandoned tasks in the list (unless --status is used).')
# Add --description flag
@click.option('--description', 'show_description', is_flag=True, default=False, help='Show the full description column in text format.')
# Add --inactive flag
@click.option('--inactive', 'include_inactive_project_tasks', is_flag=True, default=False, help='Include tasks from non-ACTIVE projects.')
@click.pass_context
# Add include_inactive_project_tasks to signature
# Signature already correct
def task_list(ctx, project: Optional[str], status: Optional[str], show_id: bool, include_completed: bool, include_abandoned: bool, show_description: bool, include_inactive_project_tasks: bool):
    """List tasks with optional filters."""
    conn = get_db_connection()
    try:
        project_id = None
        if project:
            # Resolve project identifier if provided
            project_obj = resolve_project_identifier(conn, project)
            project_id = project_obj.id

        status_enum = TaskStatus(status) if status else None
        tasks = list_tasks(conn, project_id=project_id, status=status_enum,
                           include_completed=include_completed, include_abandoned=include_abandoned, include_inactive_project_tasks=include_inactive_project_tasks)  # Pass flags

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


@task.command("show")
@click.argument("project_identifier")  # Add project identifier argument
@click.argument("task_identifier")    # Rename task_id to task_identifier
@click.pass_context
def task_show(ctx, project_identifier: str, task_identifier: str):
    """Show task details."""
    conn = get_db_connection()
    try:
        # Resolve project first, then task within that project
        project_obj = resolve_project_identifier(conn, project_identifier)
        task = resolve_task_identifier(
            conn, project_obj, task_identifier)  # Use resolver

        output_format = ctx.obj.get('FORMAT', 'json')
        # Resolver raises error if not found, so we assume task exists here
        click.echo(format_output(output_format, "success", task))
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@task.command("update")
@click.argument("project_identifier")  # Add project identifier argument
@click.argument("task_identifier")    # Rename task_id to task_identifier
@click.option("--name", help="New task name")
@click.option("--description", help="New task description (or @filepath to read from file).", callback=read_content_from_argument)
@click.option("--status", type=click.Choice([s.value for s in TaskStatus]),
              help="New task status")
# Clarify help text
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
                (See GUIDELINES.md for details)

                **When starting the next task/session:**
                - Remember to set the task status to IN_PROGRESS!
             """)
            click.echo(reminder.strip(), err=True)
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()


@task.command("delete")
@click.argument("project_identifier")  # Add project identifier argument
@click.argument("task_identifier")    # Rename task_id to task_identifier
@click.option('--force', is_flag=True, default=False, help='REQUIRED: Confirm irreversible deletion of task and associated data.')
@click.pass_context
def task_delete(ctx, project_identifier: str, task_identifier: str, force: bool):  # Add force parameter
    """Delete a task."""
    conn = get_db_connection()
    try:
        # Resolve project and task first to get the task ID
        project_obj = resolve_project_identifier(conn, project_identifier)
        task_to_delete = resolve_task_identifier(
            conn, project_obj, task_identifier)
        task_id = task_to_delete.id

        # Check for --force flag before proceeding
        if not force:
            raise click.UsageError(
                "Deleting a task is irreversible and will remove all associated subtasks, notes, etc. "
                "Use the --force flag to confirm."
            )

        success = delete_task(conn, task_id)  # Call delete with resolved ID
        output_format = ctx.obj.get('FORMAT', 'json')
        # Resolver raises error if not found, delete_task returns bool
        if success:
            click.echo(format_output(output_format, "success",
                       message=f"Task '{task_identifier}' deleted from project '{project_identifier}'"))
        else:
            # Should not be reached if resolver works
            click.echo(format_output(output_format, "error",
                       message=f"Failed to delete task '{task_identifier}'"))
    except click.ClickException:
        # Let Click handle its own exceptions (like UsageError)
        raise
    except Exception as e:  # Catch other unexpected errors
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=f"An unexpected error occurred: {e}"))
    finally:
        conn.close()


@task.group()
def dependency():
    """Manage task dependencies."""
    pass


@dependency.command("add")
@click.argument("project_identifier")  # Add project identifier argument
@click.argument("task_identifier")    # Rename task_id to task_identifier
# Clarify help
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
@click.argument("project_identifier")  # Add project identifier argument
@click.argument("task_identifier")    # Rename task_id to task_identifier
# Clarify help
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
@click.argument("project_identifier")  # Add project identifier argument
@click.argument("task_identifier")    # Rename task_id to task_identifier
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

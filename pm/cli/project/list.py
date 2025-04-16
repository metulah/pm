# pm/cli/project/list.py
import click

from ...storage import list_projects
from ..common_utils import get_db_connection, format_output


@click.command("list")  # Add the click command decorator
@click.option('--id', 'show_id', is_flag=True, default=False, help='Show the full ID column in text format.')
@click.option('--completed', 'include_completed', is_flag=True, default=False, help='Include completed projects in the list.')
@click.option('--description', 'show_description', is_flag=True, default=False, help='Show the full description column in text format.')
@click.option('--archived', 'include_archived', is_flag=True, default=False, help='Include archived projects in the list.')
@click.option('--prospective', 'include_prospective', is_flag=True, default=False, help='Include prospective projects in the list.')
@click.option('--cancelled', 'include_cancelled', is_flag=True, default=False, help='Include cancelled projects in the list.')
@click.option('--all', 'include_all', is_flag=True, default=False, help='Include projects of all statuses (overrides other status flags).')
@click.pass_context
def project_list(ctx, show_id: bool, include_completed: bool, show_description: bool, include_archived: bool, include_cancelled: bool, include_prospective: bool, include_all: bool):
    """List all projects."""
    conn = get_db_connection()
    try:
        # If --all is specified, override individual flags
        if include_all:
            include_completed = True
            include_archived = True
            include_cancelled = True
            include_prospective = True
            # Note: ACTIVE projects are included by default unless filtered out

        # Pass flags to storage function
        projects = list_projects(conn, include_completed=include_completed,
                                 include_archived=include_archived,
                                 include_cancelled=include_cancelled,
                                 include_prospective=include_prospective)
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        # Pass the show_id flag to the context for the formatter
        ctx.obj['SHOW_ID'] = show_id
        ctx.obj['SHOW_DESCRIPTION'] = show_description  # Pass flag to context
        # Pass format and list of objects
        formatted_output = format_output(output_format, "success", projects)
        click.echo(formatted_output)
    except Exception as e:
        # Get format from context
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

# pm/cli/project/show.py
import click

from ..common_utils import get_db_connection, format_output, resolve_project_identifier


@click.command("show")  # Add the click command decorator
@click.argument("identifier")
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
        click.echo(format_output(output_format, "error",
                   message=str(e)))  # Use format_output
    finally:
        conn.close()

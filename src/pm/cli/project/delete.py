# pm/cli/project/delete.py
import click

from ...storage import delete_project, ProjectNotEmptyError
from ..common_utils import get_db_connection, format_output, resolve_project_identifier


@click.command("delete")  # Add the click command decorator
@click.argument("identifier")
@click.option('--force', is_flag=True, default=False, help='REQUIRED: Confirm irreversible deletion of project and associated data.')
@click.pass_context
def project_delete(ctx, identifier: str, force: bool):
    """Delete a project."""
    conn = get_db_connection()
    try:
        # Resolve identifier first to get the project ID
        project_to_delete = resolve_project_identifier(conn, identifier)
        project_id = project_to_delete.id

        # Check for --force flag before proceeding
        if not force:
            raise click.UsageError(
                "Deleting a project is irreversible and will remove all associated tasks, notes, etc. "
                "Use the --force flag to confirm."
            )

        # Call delete_project with the resolved ID (force=True is implied by reaching here)
        success = delete_project(conn, project_id, force=True)
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
        # Original message is fine, as this error should ideally only be raised
        # by the storage layer if force=True was passed but something went wrong.
        # The CLI layer prevents calling storage without force.
        click.echo(format_output(output_format, "error", message=str(e)))
    except click.ClickException:
        # Let Click handle its own exceptions (like UsageError)
        # This ensures correct exit codes and stderr output for CLI errors
        raise
    except Exception as e:  # Catch other unexpected errors
        output_format = ctx.obj.get('FORMAT', 'json')
        click.echo(format_output(output_format, "error",
                   message=f"An unexpected error occurred: {e}"))
    finally:
        conn.close()

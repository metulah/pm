"""CLI command for initializing the PM tool in a project."""

import click
import os
import pathlib
from pm.storage import db

# Define the standard path for the PM database
DEFAULT_PM_DIR = ".pm"
DEFAULT_DB_FILENAME = "pm.db"


@click.command()
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Skip interactive confirmation.",
)
@click.pass_context
def init(ctx, yes):
    """Initializes the PM tool environment in the current directory."""
    pm_dir_path = pathlib.Path(DEFAULT_PM_DIR)
    db_path = pm_dir_path / DEFAULT_DB_FILENAME

    click.echo(f"Checking for existing initialization at {db_path}...")

    # Check if the database file already exists
    if db_path.exists():
        click.echo(
            f"Error: PM environment already initialized at {db_path}.", err=True)
        click.echo(
            "To re-initialize (use with caution!), delete the .pm directory first.")
        ctx.exit(1)  # Exit with error code

    # Proceed only if non-interactive or confirmed by user
    if not yes:
        # Display welcome message and ask for confirmation
        click.echo("\nWelcome to `pm init`!\n")
        click.echo(
            "This command will initialize the current directory for use with the pm tool."
        )
        click.echo(
            "It will create a hidden `.pm` directory and a database file (`.pm/pm.db`)"
        )
        click.echo("within it to store project and task information.\n")
        click.echo(
            "This setup allows you to manage your projects effectively using the `pm` commands.\n"
        )
        # abort=True will exit the script if the user enters 'n'
        # abort=True will exit the script if the user enters 'n'
        # default=True makes Enter key confirm
        click.confirm(
            # click.confirm automatically adds [Y/n] based on default=True
            "Is it okay to proceed?", abort=True, default=True)
        click.echo()  # Add a newline after confirmation for better spacing

    # --- Actual Initialization ---
    click.echo(f"Creating pm directory at {pm_dir_path}...")
    try:
        # exist_ok=True handles case where dir exists but db doesn't
        pm_dir_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        click.echo(f"Error creating directory {pm_dir_path}: {e}", err=True)
        ctx.exit(1)

    click.echo(f"Initializing database at {db_path}...")
    try:
        # Pass the specific path to init_db
        conn = db.init_db(db_path=str(db_path))
        conn.close()
        click.echo(
            f"Successfully initialized pm environment in {pm_dir_path}/")
        click.echo(
            "\nYou can now start managing your project. Try running `pm welcome` for guidance."
        )
    except Exception as e:
        click.echo(f"Error initializing database: {e}", err=True)
        # Attempt cleanup if initialization failed
        try:
            if db_path.exists():
                db_path.unlink()
            # Only remove dir if it's empty (safer)
            if pm_dir_path.exists() and not any(pm_dir_path.iterdir()):
                pm_dir_path.rmdir()
        except OSError as cleanup_e:
            click.echo(f"Error during cleanup: {cleanup_e}", err=True)
        ctx.exit(1)

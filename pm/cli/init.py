"""CLI command for initializing the PM tool in a project."""

import click
import os
import pathlib
from pm.storage import db

# Define the standard path for the PM database
DEFAULT_PM_DIR = ".pm"
DEFAULT_DB_FILENAME = "pm.db"


@click.command()
@click.pass_context
def init(ctx):
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

    click.echo(f"Creating PM directory at {pm_dir_path}...")
    try:
        # exist_ok=True is safer if only checking for db file, but let's be specific
        # If the dir exists but db doesn't, we want to proceed.
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
            f"Successfully initialized PM environment in {pm_dir_path}/")
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

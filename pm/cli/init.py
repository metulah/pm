"""CLI command for initializing the PM tool in a project."""

import click
import os
import pathlib
import subprocess
import sys
from pm.storage import db
# --- New Imports ---
from pm.core.guideline import get_available_guidelines
from pm.core.config import (
    load_config,
    save_config,
    get_active_guidelines,
    set_active_guidelines,
    get_config_path,  # Needed to check config existence
)
# --- End New Imports ---

# Define the standard path for the PM database
DEFAULT_PM_DIR = ".pm"
DEFAULT_DB_FILENAME = "pm.db"
GITIGNORE_COMMENT = "# PM Tool configuration directory"
GITIGNORE_IGNORE_ENTRY = ".pm/*"  # Ignore contents of .pm
GITIGNORE_ALLOW_GUIDELINES = "!.pm/guidelines/"  # Allow custom guidelines
GITIGNORE_ALLOW_CONFIG = "!.pm/config.toml"   # Allow config file
DEFAULT_ACTIVE_GUIDELINES = ["pm"]  # Default for non-interactive first run

# --- Helper Functions for Gitignore ---
# (Git helper functions remain unchanged)


def _run_git_command(command_args):
    """Runs a Git command and captures its output and exit code."""
    try:
        process = subprocess.run(
            ["git"] + command_args,
            capture_output=True,
            text=True,
            check=False,
            cwd=pathlib.Path.cwd(),
        )
        return process
    except FileNotFoundError:
        return None
    except Exception as e:
        click.echo(
            f"Warning: Error running git command: {e}", err=True, file=sys.stderr)
        return None


def _is_git_repository():
    """Checks if the current directory is inside a Git repository."""
    process = _run_git_command(["rev-parse", "--is-inside-work-tree"])
    return process is not None and process.returncode == 0 and process.stdout.strip() == "true"


def _get_git_root():
    """Gets the root directory of the Git repository."""
    process = _run_git_command(["rev-parse", "--show-toplevel"])
    if process is not None and process.returncode == 0:
        root_path_str = process.stdout.strip()
        if root_path_str:
            return pathlib.Path(root_path_str)
    return None

# --- CLI Command ---


@click.command()
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Skip interactive confirmation and guideline selection (uses defaults on first run).",
)
@click.pass_context
def init(ctx, yes):
    """Initializes the PM tool environment and configures guidelines."""
    pm_dir_path = pathlib.Path(DEFAULT_PM_DIR)
    db_path = pm_dir_path / DEFAULT_DB_FILENAME
    config_path = get_config_path()  # Get expected config path

    # Check dir path
    click.echo(f"Checking for existing initialization at {pm_dir_path}...")

    # --- Determine if already initialized ---
    db_existed_before = db_path.exists()
    # Use the function to get Path object or None
    config_path_obj = get_config_path()
    config_existed_before = config_path_obj is not None and config_path_obj.exists()

    if db_existed_before:
        click.echo(f"PM database already exists at {db_path}.")
        # Don't exit, allow re-run for config/gitignore updates
    # No else needed, logic below handles both cases

    # --- Proceed with Initialization or Update ---

    # Only show welcome and confirmation prompt on first run
    if not db_existed_before and not yes:
        click.echo("\nWelcome to `pm init`!\n")
        click.echo(
            "This command will initialize the current directory for use with the pm tool.")
        click.echo(
            f"It will create a `{DEFAULT_PM_DIR}` directory and database (`{db_path}`).")
        click.echo(
            "It will also help you configure initial project guidelines.\n")
        click.confirm("Is it okay to proceed?", abort=True, default=True)
        click.echo()

    # Actual Directory/DB Initialization (only if DB didn't exist before)
    if not db_existed_before:
        click.echo(f"Creating pm directory at {pm_dir_path}...")
        try:
            pm_dir_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            click.echo(
                f"Error creating directory {pm_dir_path}: {e}", err=True)
            ctx.exit(1)

        click.echo(f"Initializing database at {db_path}...")
        try:
            conn = db.init_db(db_path=str(db_path))
            conn.close()
            click.echo(
                f"Successfully initialized pm database in {pm_dir_path}/")
        except Exception as e:
            click.echo(f"Error initializing database: {e}", err=True)
            # Attempt cleanup only if we tried to create
            try:
                # Check if db was partially created before unlinking
                if db_path.exists():
                    db_path.unlink()
                if pm_dir_path.exists() and not any(pm_dir_path.iterdir()):
                    pm_dir_path.rmdir()
            except OSError as cleanup_e:
                click.echo(f"Error during cleanup: {cleanup_e}", err=True)
            ctx.exit(1)

    # --- Update .gitignore (Always run this check) ---
    if _is_git_repository():
        git_root = _get_git_root()
        if git_root:
            gitignore_path = git_root / ".gitignore"
            entries_to_add = f"{GITIGNORE_COMMENT}\n{GITIGNORE_IGNORE_ENTRY}\n{GITIGNORE_ALLOW_GUIDELINES}\n{GITIGNORE_ALLOW_CONFIG}\n"
            ignore_entry_exists = False
            allow_guidelines_exists = False
            allow_config_exists = False

            try:
                if gitignore_path.exists():
                    # click.echo(f"Checking {gitignore_path}...") # Reduce verbosity
                    content = gitignore_path.read_text()
                    content_lines = content.splitlines()
                    ignore_entry_exists = GITIGNORE_IGNORE_ENTRY in content_lines
                    allow_guidelines_exists = GITIGNORE_ALLOW_GUIDELINES in content_lines
                    allow_config_exists = GITIGNORE_ALLOW_CONFIG in content_lines

                    if ignore_entry_exists and allow_guidelines_exists and allow_config_exists:
                        # click.echo(f"Required PM entries already exist in {gitignore_path}.") # Reduce verbosity
                        pass  # Already up-to-date
                    else:
                        append_content = entries_to_add
                        if content and not content.endswith("\n"):
                            append_content = "\n" + append_content
                        elif content:
                            append_content = "\n" + append_content
                        with gitignore_path.open("a") as f:
                            f.write(append_content)
                        click.echo(
                            f"Updated PM tool entries in {gitignore_path}.")
                else:
                    click.echo(f"Creating {gitignore_path}...")
                    with gitignore_path.open("w") as f:
                        f.write(entries_to_add)
                    click.echo(
                        f"Created {gitignore_path} and added PM tool entries.")
            except OSError as e:
                click.echo(
                    f"Warning: Could not read or write {gitignore_path}: {e}", err=True, file=sys.stderr)
            except Exception as e:
                click.echo(
                    f"Warning: An unexpected error occurred during .gitignore update: {e}", err=True, file=sys.stderr)
        # else: # Reduce verbosity
            # click.echo("Warning: Could not determine Git repository root. Skipping .gitignore update.", err=True, file=sys.stderr)
    # else: # Reduce verbosity
        # click.echo("Not inside a Git repository. Skipping .gitignore update.")

    # --- Guideline Configuration ---
    click.echo("\nConfiguring project guidelines...")
    try:
        available_guidelines = get_available_guidelines()
        # Returns [] if config doesn't exist or key missing
        current_active_slugs = get_active_guidelines()

        if not available_guidelines:
            click.echo("No guidelines available to configure.")
        elif yes:
            # Non-interactive mode
            if not db_existed_before:
                # First run with -y, set defaults
                set_active_guidelines(DEFAULT_ACTIVE_GUIDELINES)
                click.echo(
                    f"Set default active guidelines: {DEFAULT_ACTIVE_GUIDELINES}")
            else:
                # Re-run with -y, do not change config
                click.echo(
                    "Skipping guideline configuration in non-interactive re-run.")
        else:
            # Interactive mode
            click.echo("Available guidelines:")
            for g in available_guidelines:
                click.echo(
                    f"  - {g['slug']} ({g['type']}): {g.get('title', 'No Title')}")

            click.echo(f"\nCurrently active: {current_active_slugs}")

            prompt_text = "Enter slugs of guidelines to activate (comma-separated), or press Enter to keep current"
            # Use current list as default string for the prompt
            default_prompt_value = ",".join(current_active_slugs)

            # Don't show default in prompt itself
            selected_slugs_str = click.prompt(
                prompt_text, default=default_prompt_value, show_default=False)

            # Process input
            if selected_slugs_str == default_prompt_value:
                # User pressed Enter (or entered the exact same slugs)
                if current_active_slugs:
                    # Keeping existing non-empty selection
                    click.echo("Keeping current guideline selection.")
                    final_slugs = current_active_slugs
                else:
                    # First run, user pressed Enter - apply default 'pm'
                    click.echo("Applying default guideline 'pm'.")
                    final_slugs = ["pm"]  # Apply default
            else:
                # Parse, validate, and clean the input list
                input_slugs = [
                    slug.strip() for slug in selected_slugs_str.split(',') if slug.strip()]
                valid_slugs = {g['slug'] for g in available_guidelines}
                final_slugs = []
                invalid_slugs = []
                for slug in input_slugs:
                    if slug in valid_slugs:
                        if slug not in final_slugs:  # Avoid duplicates
                            final_slugs.append(slug)
                    else:
                        invalid_slugs.append(slug)

                if invalid_slugs:
                    click.echo(
                        f"Warning: Ignoring invalid slugs: {', '.join(invalid_slugs)}", err=True)

                # Sort for consistency before saving
                final_slugs.sort()
                set_active_guidelines(final_slugs)
                click.echo(f"Set active guidelines to: {final_slugs}")

    except Exception as e:
        click.echo(f"\nError during guideline configuration: {e}", err=True)
        # Decide if this error should cause exit(1) - maybe not?

    # --- Final Message (Only shown on successful first init) ---
    click.echo("\nInitialization complete.")

    click.echo("You can now manage your project. Try running `pm welcome`.")

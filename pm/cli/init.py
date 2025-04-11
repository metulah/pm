"""CLI command for initializing the PM tool in a project."""

import click
import os
import pathlib
import subprocess
import sys
from pm.storage import db

# Define the standard path for the PM database
DEFAULT_PM_DIR = ".pm"
DEFAULT_DB_FILENAME = "pm.db"
GITIGNORE_COMMENT = "# PM Tool configuration directory"
GITIGNORE_IGNORE_ENTRY = ".pm/*"  # Ignore contents of .pm
GITIGNORE_ALLOW_GUIDELINES = "!.pm/guidelines/"  # Allow custom guidelines
GITIGNORE_ALLOW_CONFIG = "!.pm/config.toml"   # Allow config file

# --- Helper Functions for Gitignore ---


def _run_git_command(command_args):
    """Runs a Git command and captures its output and exit code."""
    try:
        # Use text=True for automatic decoding, capture_output for stdout/stderr
        # check=False to prevent raising CalledProcessError on non-zero exit
        process = subprocess.run(
            ["git"] + command_args,
            capture_output=True,
            text=True,
            check=False,
            cwd=pathlib.Path.cwd(),  # Ensure git runs in the correct directory
        )
        return process
    except FileNotFoundError:
        # Git command not found
        return None
    except Exception as e:
        # Other potential errors during subprocess execution
        click.echo(
            f"Warning: Error running git command: {e}", err=True, file=sys.stderr)
        return None


def _is_git_repository():
    """Checks if the current directory is inside a Git repository."""
    process = _run_git_command(["rev-parse", "--is-inside-work-tree"])
    # Check if process is None (command failed to run) or exit code is non-zero
    return process is not None and process.returncode == 0 and process.stdout.strip() == "true"


def _get_git_root():
    """Gets the root directory of the Git repository."""
    process = _run_git_command(["rev-parse", "--show-toplevel"])
    if process is not None and process.returncode == 0:
        # Strip whitespace/newlines from the output
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

        # --- Update .gitignore ---
        if _is_git_repository():
            git_root = _get_git_root()
            if git_root:
                gitignore_path = git_root / ".gitignore"
                # Combine ignore and allow entries with the comment
                entries_to_add = f"{GITIGNORE_COMMENT}\n{GITIGNORE_IGNORE_ENTRY}\n{GITIGNORE_ALLOW_GUIDELINES}\n{GITIGNORE_ALLOW_CONFIG}\n"
                ignore_entry_exists = False
                allow_guidelines_exists = False  # Renamed for clarity
                allow_config_exists = False     # Added for config check

                try:
                    if gitignore_path.exists():
                        click.echo(f"Checking {gitignore_path}...")
                        content = gitignore_path.read_text()
                        # Check if both entries are already present
                        # Use simple string checking. More robust parsing could be added if needed.
                        # Ensure checks look for the specific lines, potentially with surrounding newlines
                        # A simple 'in' check might be too broad if entries are substrings of others.
                        # Let's check for the exact lines for more accuracy.
                        content_lines = content.splitlines()
                        ignore_entry_exists = GITIGNORE_IGNORE_ENTRY in content_lines
                        allow_guidelines_exists = GITIGNORE_ALLOW_GUIDELINES in content_lines
                        allow_config_exists = GITIGNORE_ALLOW_CONFIG in content_lines  # Check for config rule

                        # Check if all required entries exist
                        if ignore_entry_exists and allow_guidelines_exists and allow_config_exists:
                            click.echo(
                                f"Required PM entries already exist in {gitignore_path}.")
                        else:
                            # Append the full block if either entry is missing
                            append_content = entries_to_add
                            # Ensure newline before appending if file doesn't end with one
                            if content and not content.endswith("\n"):
                                append_content = "\n" + append_content
                            # Add extra newline if appending to ensure separation
                            elif content:
                                append_content = "\n" + append_content

                            with gitignore_path.open("a") as f:
                                f.write(append_content)
                            click.echo(
                                f"Appended PM tool entries to {gitignore_path}.")
                    else:
                        click.echo(f"Creating {gitignore_path}...")
                        with gitignore_path.open("w") as f:
                            f.write(entries_to_add)  # Write the combined block
                        click.echo(
                            f"Created {gitignore_path} and added PM tool entries.")

                except OSError as e:
                    click.echo(
                        f"Warning: Could not read or write {gitignore_path}: {e}", err=True, file=sys.stderr)
                except Exception as e:  # Catch other potential errors
                    click.echo(
                        f"Warning: An unexpected error occurred during .gitignore update: {e}", err=True, file=sys.stderr)
            else:
                click.echo(
                    "Warning: Could not determine Git repository root. Skipping .gitignore update.", err=True, file=sys.stderr)
        else:
            # Not a git repo, or git command failed
            click.echo(
                "Not inside a Git repository. Skipping .gitignore update.")

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

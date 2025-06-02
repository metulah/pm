import os
import pathlib
from click.testing import CliRunner
from pm.cli import cli  # Assuming your main CLI entry point is here
# Removed incorrect import of init_project

# No need for the old fixture, CliRunner's isolated_filesystem is better here


def test_run_from_project_root():
    """Test running a command from the project root."""
    runner = CliRunner()
    with runner.isolated_filesystem() as tmpdir:
        # Initialize a pm project using the CLI command
        init_result = runner.invoke(cli, ['init', '--yes'])  # Use --yes flag
        assert init_result.exit_code == 0
        assert os.path.isdir(os.path.join(tmpdir, ".pm"))
        assert os.path.isfile(os.path.join(tmpdir, ".pm", "pm.db"))

        # Run a command from the root
        result = runner.invoke(cli, ['project', 'list'])
        assert result.exit_code == 0
        # Check for expected output (e.g., headers or "No items found")
        assert "SLUG" in result.output or "No items found" in result.output


def test_run_from_subdirectory():
    """Test running a command from a subdirectory within the project."""
    runner = CliRunner()
    with runner.isolated_filesystem() as tmpdir:
        # Initialize a pm project using the CLI command
        init_result = runner.invoke(cli, ['init', '--yes'])  # Use --yes flag
        assert init_result.exit_code == 0
        assert os.path.isdir(os.path.join(tmpdir, ".pm"))

        # Create and move into a subdirectory
        subdir_path = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir_path)
        os.chdir(subdir_path)  # Change CWD for the test

        # Run a command from the subdirectory
        result = runner.invoke(cli, ['project', 'list'])
        assert result.exit_code == 0
        assert "SLUG" in result.output or "No items found" in result.output


def test_run_outside_project():
    """Test running a command from outside a project directory."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Do NOT initialize a project here

        # Run a command
        result = runner.invoke(cli, ['project', 'list'])

        # Assert failure and the specific error message (now without the "Error: " prefix from ClickException)
        assert result.exit_code != 0
        # ClickException prints to stderr, which is mixed into output by default runner
        assert "Not inside a pm project directory" in result.output


def test_init_creates_pm_dir_and_db():
    """Verify that 'pm init' creates the .pm directory and db file."""
    runner = CliRunner()
    with runner.isolated_filesystem() as tmpdir:
        result = runner.invoke(cli, ['init', '--yes'])  # Use --yes flag
        assert result.exit_code == 0
        pm_dir = pathlib.Path(tmpdir) / ".pm"
        db_file = pm_dir / "pm.db"
        assert pm_dir.is_dir()
        assert db_file.is_file()
        # Check the updated success message from init.py
        assert "Successfully initialized pm database" in result.output

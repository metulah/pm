import pytest
import os
from pathlib import Path
from click.testing import CliRunner

# Import the main cli entry point
from pm.cli.base import cli

# Define expected paths and messages
PM_DIR_NAME = ".pm"
DB_FILENAME = "pm.db"
SUCCESS_MSG_SNIPPET = "Successfully initialized pm environment"  # Use lowercase 'pm'
ALREADY_INIT_MSG_SNIPPET = "already initialized"
WELCOME_MSG_SNIPPET = "Welcome to `pm init`!"
CONFIRM_PROMPT_SNIPPET = "Is it okay to proceed? [Y/n]:"
ABORT_MSG = "Aborted!"
NEXT_STEPS_MSG_SNIPPET = "Try running `pm welcome` for guidance."


@pytest.fixture(scope="module")
def runner():
    """Provides a Click CliRunner with separated stderr."""
    # mix_stderr=False is important to capture stderr separately for errors
    return CliRunner(mix_stderr=False)


def test_init_success_non_interactive(runner: CliRunner, tmp_path: Path):
    """Test successful `pm init -y` (non-interactive)."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # Use -y flag
        result = runner.invoke(cli, ['init', '-y'], catch_exceptions=False)

        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

        assert result.exit_code == 0, f"CLI Error: {result.stderr or result.stdout}"
        assert result.stderr == ""  # No errors expected on stderr
        assert SUCCESS_MSG_SNIPPET in result.stdout
        # Ensure interactive elements are NOT present
        assert WELCOME_MSG_SNIPPET not in result.stdout
        assert CONFIRM_PROMPT_SNIPPET not in result.stdout
        assert NEXT_STEPS_MSG_SNIPPET in result.stdout  # Check for next steps hint

        # Verify directory and file creation
        pm_dir = tmp_path / PM_DIR_NAME
        db_file = pm_dir / DB_FILENAME
        assert pm_dir.is_dir()
        assert db_file.is_file()
        assert db_file.stat().st_size > 0

    finally:
        os.chdir(original_cwd)  # Ensure we change back


def test_init_already_initialized_non_interactive(runner: CliRunner, tmp_path: Path):
    """Test running `pm init -y` when already initialized."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # First run (non-interactive, should succeed)
        result1 = runner.invoke(cli, ['init', '-y'], catch_exceptions=False)
        assert result1.exit_code == 0, "First init -y failed unexpectedly"
        assert (tmp_path / PM_DIR_NAME /
                DB_FILENAME).is_file(), "DB file not created on first run"

        # Second run (non-interactive, should fail)
        result2 = runner.invoke(cli, ['init', '-y'], catch_exceptions=False)

        print("STDOUT (second run -y):", result2.stdout)
        print("STDERR (second run -y):", result2.stderr)

        assert result2.exit_code == 1, "Second init -y should fail with exit code 1"
        # Ensure interactive/success messages are NOT printed
        assert SUCCESS_MSG_SNIPPET not in result2.stdout
        assert WELCOME_MSG_SNIPPET not in result2.stdout
        assert CONFIRM_PROMPT_SNIPPET not in result2.stdout
        # Error message expected on stderr
        assert ALREADY_INIT_MSG_SNIPPET in result2.stderr
        # Check relative path mentioned in the error message
        expected_path_in_error = f"{PM_DIR_NAME}/{DB_FILENAME}"
        assert expected_path_in_error in result2.stderr

    finally:
        os.chdir(original_cwd)  # Ensure we change back


def test_init_success_interactive_confirm(runner: CliRunner, tmp_path: Path):
    """Test successful `pm init` interactively confirming with 'y'."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # Provide 'y' and newline as input
        result = runner.invoke(
            cli, ['init'], input='y\n', catch_exceptions=False)

        print("STDOUT (interactive y):", result.stdout)
        print("STDERR (interactive y):", result.stderr)

        assert result.exit_code == 0, f"CLI Error: {result.stderr or result.stdout}"
        assert result.stderr == ""
        # Check for interactive elements and success message
        assert WELCOME_MSG_SNIPPET in result.stdout
        assert CONFIRM_PROMPT_SNIPPET in result.stdout
        assert SUCCESS_MSG_SNIPPET in result.stdout
        assert NEXT_STEPS_MSG_SNIPPET in result.stdout  # Check for next steps hint

        # Verify directory and file creation
        pm_dir = tmp_path / PM_DIR_NAME
        db_file = pm_dir / DB_FILENAME
        assert pm_dir.is_dir()
        assert db_file.is_file()
        assert db_file.stat().st_size > 0

    finally:
        os.chdir(original_cwd)


def test_init_success_interactive_default(runner: CliRunner, tmp_path: Path):
    """Test successful `pm init` interactively confirming with Enter (default)."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # Provide just newline as input (defaults to 'Y')
        result = runner.invoke(
            cli, ['init'], input='\n', catch_exceptions=False)

        print("STDOUT (interactive default):", result.stdout)
        print("STDERR (interactive default):", result.stderr)

        assert result.exit_code == 0, f"CLI Error: {result.stderr or result.stdout}"
        assert result.stderr == ""
        # Check for interactive elements and success message
        assert WELCOME_MSG_SNIPPET in result.stdout
        assert CONFIRM_PROMPT_SNIPPET in result.stdout
        assert SUCCESS_MSG_SNIPPET in result.stdout
        assert NEXT_STEPS_MSG_SNIPPET in result.stdout  # Check for next steps hint

        # Verify directory and file creation
        pm_dir = tmp_path / PM_DIR_NAME
        db_file = pm_dir / DB_FILENAME
        assert pm_dir.is_dir()
        assert db_file.is_file()
        assert db_file.stat().st_size > 0

    finally:
        os.chdir(original_cwd)


def test_init_interactive_abort(runner: CliRunner, tmp_path: Path):
    """Test aborting `pm init` interactively with 'n'."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # Provide 'n' and newline as input
        result = runner.invoke(
            cli, ['init'], input='n\n', catch_exceptions=False)

        print("STDOUT (interactive n):", result.stdout)
        # click.confirm(abort=True) prints "Aborted!" to stderr
        print("STDERR (interactive n):", result.stderr)

        # click.confirm with abort=True raises click.Abort, runner catches this -> exit_code 1
        assert result.exit_code == 1, "Interactive abort should result in exit code 1"
        # Check for interactive elements
        assert WELCOME_MSG_SNIPPET in result.stdout
        assert CONFIRM_PROMPT_SNIPPET in result.stdout
        # Check for abort message (usually on stderr for click.confirm(abort=True))
        # Note: Depending on exact click version/behavior, might be stdout. Adjust if needed.
        assert ABORT_MSG in result.stderr or ABORT_MSG in result.stdout

        # CRITICAL: Verify directory and file were NOT created
        pm_dir = tmp_path / PM_DIR_NAME
        db_file = pm_dir / DB_FILENAME
        assert not pm_dir.exists()
        assert not db_file.exists()

    finally:
        os.chdir(original_cwd)

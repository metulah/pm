import pytest
import os
from pathlib import Path
from click.testing import CliRunner

# Import the main cli entry point
from pm.cli.base import cli

# Define expected paths and messages
PM_DIR_NAME = ".pm"
DB_FILENAME = "pm.db"
SUCCESS_MSG_SNIPPET = "Successfully initialized PM environment"
ALREADY_INIT_MSG_SNIPPET = "already initialized"


@pytest.fixture(scope="module")
def runner():
    """Provides a Click CliRunner with separated stderr."""
    # mix_stderr=False is important to capture stderr separately for errors
    return CliRunner(mix_stderr=False)


def test_init_success(runner: CliRunner, tmp_path: Path):
    """Test successful `pm init` in an empty directory."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        result = runner.invoke(cli, ['init'], catch_exceptions=False)

        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

        assert result.exit_code == 0, f"CLI Error: {result.stderr or result.stdout}"
        assert result.stderr == ""  # No errors expected on stderr
        assert SUCCESS_MSG_SNIPPET in result.stdout

        # Verify directory and file creation
        pm_dir = tmp_path / PM_DIR_NAME
        db_file = pm_dir / DB_FILENAME
        assert pm_dir.is_dir()
        assert db_file.is_file()
        # Could add a check for db file size > 0 if needed
        assert db_file.stat().st_size > 0

    finally:
        os.chdir(original_cwd)  # Ensure we change back


def test_init_already_initialized(runner: CliRunner, tmp_path: Path):
    """Test running `pm init` when the directory is already initialized."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # First run (should succeed)
        result1 = runner.invoke(cli, ['init'], catch_exceptions=False)
        assert result1.exit_code == 0, "First init failed unexpectedly"
        assert (tmp_path / PM_DIR_NAME /
                DB_FILENAME).is_file(), "DB file not created on first run"

        # Second run (should fail)
        result2 = runner.invoke(cli, ['init'], catch_exceptions=False)

        print("STDOUT (second run):", result2.stdout)
        print("STDERR (second run):", result2.stderr)

        assert result2.exit_code == 1, "Second init should fail with exit code 1"
        # Ensure success message is NOT printed
        assert SUCCESS_MSG_SNIPPET not in result2.stdout
        # Error message expected on stderr
        assert ALREADY_INIT_MSG_SNIPPET in result2.stderr
        # Check relative path mentioned in the error message
        expected_path_in_error = f"{PM_DIR_NAME}/{DB_FILENAME}"
        assert expected_path_in_error in result2.stderr

    finally:
        os.chdir(original_cwd)  # Ensure we change back

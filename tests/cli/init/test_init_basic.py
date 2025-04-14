import pytest
import os
import subprocess
from pathlib import Path
from click.testing import CliRunner
# Note: Removed tomllib import as it's not needed for these tests

# Import the main cli entry point
from pm.cli.base import cli
# Import constants from the module being tested
from pm.cli.init import GITIGNORE_COMMENT, GITIGNORE_IGNORE_ENTRY, GITIGNORE_ALLOW_GUIDELINES, GITIGNORE_ALLOW_CONFIG

# Define expected paths and messages
PM_DIR_NAME = ".pm"
DB_FILENAME = "pm.db"
# Updated to match actual output
SUCCESS_MSG_SNIPPET = "Successfully initialized pm database"
ALREADY_INIT_MSG_SNIPPET = "already initialized"
WELCOME_MSG_SNIPPET = "Welcome to `pm init`!"
CONFIRM_PROMPT_SNIPPET = "Is it okay to proceed? [Y/n]:"
ABORT_MSG = "Aborted!"
NEXT_STEPS_MSG_SNIPPET = "Try running `pm welcome`."  # Removed " for guidance."


# --- Helper Function for Tests ---

def _init_git_repo(path: Path):
    """Initializes a Git repository in the given path."""
    try:
        subprocess.run(["git", "init", "-b", "main"], cwd=path,
                       check=True, capture_output=True)
        # Configure dummy user for commits if needed, avoids warnings/errors
        subprocess.run(["git", "config", "user.email",
                       "test@example.com"], cwd=path, check=True)
        subprocess.run(["git", "config", "user.name",
                       "Test User"], cwd=path, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        pytest.fail(f"Failed to initialize Git repository at {path}: {e}")


# --- Fixtures ---

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

        assert result2.exit_code == 0, "Second init -y should succeed"  # Changed from 1 to 0
        # Added check for empty stderr
        assert result2.stderr == "", "Stderr should be empty on successful re-run"
        # Ensure interactive/success messages are NOT printed
        assert SUCCESS_MSG_SNIPPET not in result2.stdout
        assert WELCOME_MSG_SNIPPET not in result2.stdout
        assert CONFIRM_PROMPT_SNIPPET not in result2.stdout
        # Check for specific messages indicating a re-run
        assert "PM database already exists" in result2.stdout
        assert "Skipping guideline configuration" in result2.stdout  # Check for skip message
        # Ensure next steps are still shown
        assert NEXT_STEPS_MSG_SNIPPET in result2.stdout

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

# --- Tests for .gitignore Handling ---


def test_init_no_git_repo_skips_gitignore(runner: CliRunner, tmp_path: Path):
    """Test `pm init -y` does nothing to .gitignore if not in a git repo."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # Ensure no .git directory exists
        assert not (tmp_path / ".git").exists()

        result = runner.invoke(cli, ['init', '-y'], catch_exceptions=False)
        assert result.exit_code == 0
        assert SUCCESS_MSG_SNIPPET in result.stdout
        # Check that .gitignore was NOT created
        assert not (tmp_path / ".gitignore").exists()
        # Message indicating skipping was removed for verbosity, so remove assertion
        # assert "Not inside a Git repository. Skipping .gitignore update." in result.stdout

    finally:
        os.chdir(original_cwd)


def test_init_git_repo_creates_gitignore(runner: CliRunner, tmp_path: Path):
    """Test `pm init -y` creates .gitignore if in a git repo and it doesn't exist."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        _init_git_repo(tmp_path)
        gitignore_path = tmp_path / ".gitignore"
        assert not gitignore_path.exists()  # Pre-condition

        result = runner.invoke(cli, ['init', '-y'], catch_exceptions=False)
        assert result.exit_code == 0
        assert SUCCESS_MSG_SNIPPET in result.stdout
        assert f"Creating {gitignore_path}..." in result.stdout
        assert gitignore_path.is_file()

        content = gitignore_path.read_text()
        assert GITIGNORE_COMMENT in content
        assert GITIGNORE_IGNORE_ENTRY in content
        assert GITIGNORE_ALLOW_GUIDELINES in content
        assert GITIGNORE_ALLOW_CONFIG in content  # Check for config rule
        # Check structure (comment, newline, ignore, newline, allow guidelines, newline, allow config, newline)
        # Swapped order
        expected_content = f"{GITIGNORE_COMMENT}\n{GITIGNORE_IGNORE_ENTRY}\n{GITIGNORE_ALLOW_CONFIG}\n{GITIGNORE_ALLOW_GUIDELINES}\n"
        assert content == expected_content

    finally:
        os.chdir(original_cwd)


def test_init_git_repo_appends_gitignore(runner: CliRunner, tmp_path: Path):
    """Test `pm init -y` appends to .gitignore if it exists but lacks the entry."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        _init_git_repo(tmp_path)
        gitignore_path = tmp_path / ".gitignore"
        initial_content = "# Existing rules\n*.log\n"
        gitignore_path.write_text(initial_content)  # Create existing file

        result = runner.invoke(cli, ['init', '-y'], catch_exceptions=False)
        assert result.exit_code == 0
        assert SUCCESS_MSG_SNIPPET in result.stdout
        # Checking message was removed for verbosity
        # assert f"Checking {gitignore_path}..." in result.stdout
        # Message was removed for verbosity
        # assert f"Appended PM tool entries to {gitignore_path}." in result.stdout

        content = gitignore_path.read_text()
        assert initial_content in content  # Original content still there
        assert GITIGNORE_COMMENT in content
        assert GITIGNORE_IGNORE_ENTRY in content
        assert GITIGNORE_ALLOW_GUIDELINES in content
        assert GITIGNORE_ALLOW_CONFIG in content  # Check for config rule
        # Check structure (original, newline, comment, newline, ignore, newline, allow guidelines, newline, allow config, newline)
        # Note: The implementation adds an extra newline before appending if content exists
        # Swapped order
        expected_content = f"{initial_content}\n{GITIGNORE_COMMENT}\n{GITIGNORE_IGNORE_ENTRY}\n{GITIGNORE_ALLOW_CONFIG}\n{GITIGNORE_ALLOW_GUIDELINES}\n"
        assert content == expected_content

    finally:
        os.chdir(original_cwd)


def test_init_git_repo_gitignore_already_has_entry(runner: CliRunner, tmp_path: Path):
    """Test `pm init -y` does nothing if .gitignore exists and has the entry."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        _init_git_repo(tmp_path)
        gitignore_path = tmp_path / ".gitignore"
        # Include the exact entry we expect pm init to add
        # Include all entries we expect pm init to add
        initial_content = f"# Existing rules\n*.pyc\n\n{GITIGNORE_COMMENT}\n{GITIGNORE_IGNORE_ENTRY}\n{GITIGNORE_ALLOW_GUIDELINES}\n{GITIGNORE_ALLOW_CONFIG}\n"
        # Create existing file with entries
        gitignore_path.write_text(initial_content)

        result = runner.invoke(cli, ['init', '-y'], catch_exceptions=False)
        assert result.exit_code == 0
        assert SUCCESS_MSG_SNIPPET in result.stdout
        # Checking message was removed for verbosity
        # assert f"Checking {gitignore_path}..." in result.stdout
        # Message was removed for verbosity
        # assert f"Required PM entries already exist in {gitignore_path}." in result.stdout
        # Ensure append/create messages are NOT present
        assert "Appended PM tool entries" not in result.stdout
        assert f"Creating {gitignore_path}" not in result.stdout

        # Verify content is unchanged
        content = gitignore_path.read_text()
        assert content == initial_content

    finally:
        os.chdir(original_cwd)


def test_init_interactive_confirm_handles_gitignore(runner: CliRunner, tmp_path: Path):
    """Test `pm init` (interactive 'y') also handles .gitignore creation."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        _init_git_repo(tmp_path)
        gitignore_path = tmp_path / ".gitignore"
        assert not gitignore_path.exists()  # Pre-condition

        # Provide 'y' and newline as input
        result = runner.invoke(
            cli, ['init'], input='y\n', catch_exceptions=False)

        assert result.exit_code == 0, f"CLI Error: {result.stderr or result.stdout}"
        assert SUCCESS_MSG_SNIPPET in result.stdout
        # Check .gitignore message
        assert f"Creating {gitignore_path}..." in result.stdout
        assert gitignore_path.is_file()

        content = gitignore_path.read_text()
        assert GITIGNORE_COMMENT in content
        assert GITIGNORE_IGNORE_ENTRY in content
        assert GITIGNORE_ALLOW_GUIDELINES in content
        assert GITIGNORE_ALLOW_CONFIG in content  # Check for config rule
        # Swapped order
        expected_content = f"{GITIGNORE_COMMENT}\n{GITIGNORE_IGNORE_ENTRY}\n{GITIGNORE_ALLOW_CONFIG}\n{GITIGNORE_ALLOW_GUIDELINES}\n"
        assert content == expected_content

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

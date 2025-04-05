# tests/test_cli_welcome.py
import pytest
from click.testing import CliRunner
from pathlib import Path
import os

# Import the main cli entry point from base where 'welcome' was added
from pm.cli.base import cli

# Define expected content snippets (adjust if actual content changes)
# Assuming these files exist in pm/resources/
RESOURCES_DIR = Path(__file__).parent.parent / 'pm' / 'resources'
DEFAULT_GUIDELINE_PATH = RESOURCES_DIR / 'welcome_guidelines_default.md'
# SOFTWARE_GUIDELINE_PATH = RESOURCES_DIR / 'welcome_guidelines_software.md' # Removed
CODING_GUIDELINE_PATH = RESOURCES_DIR / 'welcome_guidelines_coding.md'
VCS_GUIDELINE_PATH = RESOURCES_DIR / 'welcome_guidelines_vcs.md'
TESTING_GUIDELINE_PATH = RESOURCES_DIR / 'welcome_guidelines_testing.md'

# Read actual snippets to make tests less brittle to minor wording changes
# Use more unique snippets if possible
DEFAULT_CONTENT_SNIPPET = "Effectively through its CLI interface."  # Fallback
# Define snippets for new guidelines
CODING_CONTENT_SNIPPET = "Follow the project's coding standards"  # Fallback
VCS_CONTENT_SNIPPET = "Commit changes frequently"  # Fallback
TESTING_CONTENT_SNIPPET = "Write and/or update tests"  # Fallback
try:
    if DEFAULT_GUIDELINE_PATH.is_file():
        default_lines = DEFAULT_GUIDELINE_PATH.read_text(
            encoding='utf-8').splitlines()
        # Use a snippet likely to remain stable
        DEFAULT_CONTENT_SNIPPET = next(
            (line for line in default_lines if 'Examine current state:' in line), DEFAULT_CONTENT_SNIPPET)
    if CODING_GUIDELINE_PATH.is_file():
        CODING_CONTENT_SNIPPET = CODING_GUIDELINE_PATH.read_text(
            encoding='utf-8').splitlines()[-1].strip()  # Get the last line
    if VCS_GUIDELINE_PATH.is_file():
        # Get the first bullet point (line index 2)
        vcs_lines = VCS_GUIDELINE_PATH.read_text(encoding='utf-8').splitlines()
        if len(vcs_lines) > 2:
            # Use line index 6 for a more specific snippet
            VCS_CONTENT_SNIPPET = vcs_lines[6].strip()
    if TESTING_GUIDELINE_PATH.is_file():
        # Get the first bullet point (line index 2)
        testing_lines = TESTING_GUIDELINE_PATH.read_text(
            encoding='utf-8').splitlines()
        if len(testing_lines) > 2:
            # Use line index 6 for a more specific snippet
            TESTING_CONTENT_SNIPPET = testing_lines[6].strip()
except Exception:
    print("Warning: Could not read guideline files for test snippets. Using fallbacks.")
    pass  # Keep fallback if reading fails during test setup

CUSTOM_FILE_CONTENT = "This is a custom guideline from a test file."
SEPARATOR = "\n\n<<<--- GUIDELINE SEPARATOR --->>>\n\n"  # Define a unique separator


@pytest.fixture(scope="module")
def runner():
    """Provides a Click CliRunner with separated stderr."""
    # mix_stderr=False is important to capture stderr separately for warnings
    return CliRunner(mix_stderr=False)


@pytest.fixture(scope="function")
def temp_guideline_file(tmp_path):
    """Creates a temporary guideline file for testing @path."""
    file_path = tmp_path / "custom_guidelines.md"
    file_path.write_text(CUSTOM_FILE_CONTENT, encoding='utf-8')
    yield file_path  # Use yield to ensure cleanup if needed, though tmp_path handles it

# --- Test Cases ---


def test_welcome_default(runner: CliRunner):
    """Test `pm welcome` shows only default guidelines."""
    # This test should PASS with the current (non-collating) implementation
    result = runner.invoke(cli, ['welcome'])
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0
    assert DEFAULT_CONTENT_SNIPPET in result.stdout
    # No need to check for absence of other built-ins here, focus is on default only
    # assert CODING_CONTENT_SNIPPET not in result.stdout # etc.
    assert CUSTOM_FILE_CONTENT not in result.stdout
    assert SEPARATOR not in result.stdout  # Check for the *unique* separator
    assert result.stderr == ""  # No warnings expected


def test_welcome_builtin_coding_collated(runner: CliRunner):
    """Test `pm welcome -g coding` shows default + coding (collated)."""
    result = runner.invoke(cli, ['welcome', '--guidelines', 'coding'])
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0
    assert DEFAULT_CONTENT_SNIPPET in result.stdout
    assert CODING_CONTENT_SNIPPET in result.stdout
    assert VCS_CONTENT_SNIPPET not in result.stdout  # Ensure others aren't included
    assert TESTING_CONTENT_SNIPPET not in result.stdout
    assert CUSTOM_FILE_CONTENT not in result.stdout
    assert SEPARATOR in result.stdout  # Expect separator
    assert result.stderr == ""  # No warnings expected


def test_welcome_builtin_vcs_collated(runner: CliRunner):
    """Test `pm welcome -g vcs` shows default + vcs (collated)."""
    result = runner.invoke(cli, ['welcome', '--guidelines', 'vcs'])
    assert result.exit_code == 0
    assert DEFAULT_CONTENT_SNIPPET in result.stdout
    assert VCS_CONTENT_SNIPPET in result.stdout
    assert CODING_CONTENT_SNIPPET not in result.stdout
    assert result.stderr == ""


def test_welcome_builtin_testing_collated(runner: CliRunner):
    """Test `pm welcome -g testing` shows default + testing (collated)."""
    result = runner.invoke(cli, ['welcome', '--guidelines', 'testing'])
    assert result.exit_code == 0
    assert DEFAULT_CONTENT_SNIPPET in result.stdout
    assert TESTING_CONTENT_SNIPPET in result.stdout
    assert CODING_CONTENT_SNIPPET not in result.stdout
    assert result.stderr == ""


def test_welcome_custom_file_collated(runner: CliRunner, temp_guideline_file: Path):
    """Test `pm welcome -g @<path>` shows default + custom file (collated)."""
    # NOTE: This test assumes the implementation uses -g or --guidelines and @ prefix
    # It will FAIL until the welcome.py code is updated for collation
    arg = f"@{temp_guideline_file}"
    result = runner.invoke(cli, ['welcome', '--guidelines', arg])
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0
    assert DEFAULT_CONTENT_SNIPPET in result.stdout
    assert CODING_CONTENT_SNIPPET not in result.stdout  # Check absence of others
    assert CUSTOM_FILE_CONTENT in result.stdout
    assert SEPARATOR in result.stdout  # Expect separator
    assert result.stderr == ""  # No warnings expected


def test_welcome_builtin_coding_and_file_collated(runner: CliRunner, temp_guideline_file: Path):
    """Test `pm welcome -g coding -g @<path>` shows default + coding + file (collated)."""
    arg = f"@{temp_guideline_file}"
    result = runner.invoke(
        cli, ['welcome', '--guidelines', 'coding', '--guidelines', arg])
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0
    assert DEFAULT_CONTENT_SNIPPET in result.stdout
    assert CODING_CONTENT_SNIPPET in result.stdout  # Check for coding
    assert CUSTOM_FILE_CONTENT in result.stdout
    assert VCS_CONTENT_SNIPPET not in result.stdout  # Check absence of others
    assert result.stdout.count(SEPARATOR) == 2  # Expect two separators
    assert result.stderr == ""  # No warnings expected


def test_welcome_all_builtins_collated(runner: CliRunner):
    """Test `pm welcome -g coding -g vcs -g testing` shows all."""
    result = runner.invoke(cli, ['welcome', '--guidelines',
                           'coding', '--guidelines', 'vcs', '--guidelines', 'testing'])
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0
    assert DEFAULT_CONTENT_SNIPPET in result.stdout
    assert CODING_CONTENT_SNIPPET in result.stdout
    assert VCS_CONTENT_SNIPPET in result.stdout
    assert TESTING_CONTENT_SNIPPET in result.stdout
    assert CUSTOM_FILE_CONTENT not in result.stdout
    assert result.stdout.count(SEPARATOR) == 3  # Expect three separators
    assert result.stderr == ""


def test_welcome_non_existent_name_collated(runner: CliRunner):
    """Test `pm welcome -g non_existent` shows default + warning (collated)."""
    # NOTE: This test assumes the implementation uses -g or --guidelines
    # It will FAIL until the welcome.py code is updated for collation
    result = runner.invoke(
        cli, ['welcome', '--guidelines', 'non_existent_name'])
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 1  # Should fail due to explicit source error
    assert result.stdout == ""  # No output should be generated
    # assert SOFTWARE_CONTENT_SNIPPET not in result.stdout # Remove check for old snippet
    # Assertions for content absence are now covered by checking for empty stdout
    # assert SOFTWARE_CONTENT_SNIPPET not in result.stdout
    # assert CUSTOM_FILE_CONTENT not in result.stdout
    # assert SEPARATOR not in result.stdout
    # Check for specific warning message structure
    assert "Warning: Could not find or read guideline source 'non_existent_name'" in result.stderr


def test_welcome_non_existent_file_collated(runner: CliRunner, tmp_path: Path):
    """Test `pm welcome -g @non_existent_path` shows default + warning (collated)."""
    # NOTE: This test assumes the implementation uses -g or --guidelines and @ prefix
    # It will FAIL until the welcome.py code is updated for collation
    non_existent_path = tmp_path / "no_such_file.md"
    arg = f"@{non_existent_path}"
    result = runner.invoke(cli, ['welcome', '--guidelines', arg])
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 1  # Should fail due to explicit source error
    assert result.stdout == ""  # No output should be generated
    # assert SOFTWARE_CONTENT_SNIPPET not in result.stdout # Remove check for old snippet
    # Assertions for content absence are now covered by checking for empty stdout
    # assert SOFTWARE_CONTENT_SNIPPET not in result.stdout
    # assert CUSTOM_FILE_CONTENT not in result.stdout
    # assert SEPARATOR not in result.stdout
    # Check for specific warning message structure including the @ prefix
    assert f"Warning: Could not find or read guideline source '{arg}'" in result.stderr


def test_welcome_multiple_errors_collated(runner: CliRunner, tmp_path: Path):
    """Test `pm welcome -g bad_name -g @bad_path` shows default + multiple warnings (collated)."""
    # NOTE: This test assumes the implementation uses -g or --guidelines and @ prefix
    # It will FAIL until the welcome.py code is updated for collation
    non_existent_path = tmp_path / "no_such_file.md"
    arg_file = f"@{non_existent_path}"
    arg_name = "bad_name"
    result = runner.invoke(
        cli, ['welcome', '--guidelines', arg_name, '--guidelines', arg_file])
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 1  # Should fail due to explicit source error
    assert result.stdout == ""  # No output should be generated
    # assert SOFTWARE_CONTENT_SNIPPET not in result.stdout # Remove check for old snippet
    # Assertions for content absence are now covered by checking for empty stdout
    # assert SOFTWARE_CONTENT_SNIPPET not in result.stdout
    # assert CUSTOM_FILE_CONTENT not in result.stdout
    # assert SEPARATOR not in result.stdout
    # Check that *both* warning messages are present in stderr
    assert f"Warning: Could not find or read guideline source '{arg_name}'" in result.stderr
    assert f"Warning: Could not find or read guideline source '{arg_file}'" in result.stderr
    # The previous assertion `assert result.stderr == ""` was incorrect and has been removed.
# Remove the test for the old positional argument behavior as it's deprecated
# def test_welcome_original_behavior_software(runner: CliRunner):
#     ...
    assert CUSTOM_FILE_CONTENT not in result.stdout
    assert SEPARATOR not in result.stdout
    # assert result.stderr == "" # This assertion was incorrect and is now removed.

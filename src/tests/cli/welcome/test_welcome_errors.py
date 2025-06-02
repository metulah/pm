# tests/cli/welcome/test_welcome_errors.py
from click.testing import CliRunner
from pathlib import Path
import os

# Import the main cli entry point
from pm.cli.__main__ import cli

# Import constants and fixtures from conftest
from .conftest import (
    DEFAULT_CONTENT_SNIPPET,
    SEPARATOR  # Needed for some error tests involving config
)


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
    # Check updated warning
    # Check updated warning
    assert "Warning: Could not find guideline source 'non_existent_name' (Not found as built-in or custom file name)." in result.stderr


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
    # Check for specific warning message structure
    # Check updated warning format
    assert f"Warning: Could not find or read guideline source '@{non_existent_path}'" in result.stderr


def test_welcome_multiple_errors_collated(runner: CliRunner, tmp_path: Path):
    """Test `pm welcome` with multiple invalid guidelines shows all warnings."""
    # NOTE: This test assumes the implementation uses -g or --guidelines and @ prefix
    # It will FAIL until the welcome.py code is updated for collation
    non_existent_path = tmp_path / "no_such_file.md"
    arg_file = f"@{non_existent_path}"
    arg_name = "bad_name"
    result = runner.invoke(
        cli, ['welcome', '--guidelines', arg_name, '--guidelines', arg_file])
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 1  # Should fail due to explicit source errors
    assert result.stdout == ""  # No output should be generated
    # assert SOFTWARE_CONTENT_SNIPPET not in result.stdout # Remove check for old snippet
    # Assertions for content absence are now covered by checking for empty stdout
    # assert SOFTWARE_CONTENT_SNIPPET not in result.stdout
    # assert CUSTOM_FILE_CONTENT not in result.stdout
    # assert SEPARATOR not in result.stdout
    # Check for both warning messages
    # Check updated warnings format
    assert "Warning: Could not find guideline source 'bad_name'" in result.stderr
    assert f"Warning: Could not find or read guideline source '@{non_existent_path}'" in result.stderr
    assert "Error: One or more specified guidelines could not be loaded." in result.stderr


def test_welcome_custom_guideline_by_name_succeeds(runner: CliRunner, tmp_path: Path):
    """Test loading a custom guideline by filename (without '@') succeeds."""
    # Create a custom guideline file in the expected location
    custom_dir = tmp_path / ".pm" / "guidelines"
    custom_dir.mkdir(parents=True, exist_ok=True)
    custom_filename = "my_custom.md"
    custom_file = custom_dir / custom_filename
    custom_content = "This is my custom guideline."
    custom_file.write_text(custom_content, encoding='utf-8')

    original_cwd = Path.cwd()
    os.chdir(tmp_path)
    try:
        # Try loading by name 'my_custom' (should now succeed by finding the file)
        result_name = runner.invoke(cli, ['welcome', '-g', 'my_custom'])
        # Try loading by relative path without '@' (should also succeed)
        result_path = runner.invoke(
            cli, ['welcome', '-g', f'.pm/guidelines/{custom_filename}'])
    finally:
        os.chdir(original_cwd)

    # Test loading by name 'my_custom'
    print("STDOUT (by name):", result_name.stdout)
    print("STDERR (by name):", result_name.stderr)
    assert result_name.exit_code == 0
    assert result_name.stderr == ""
    assert DEFAULT_CONTENT_SNIPPET in result_name.stdout  # Default is included
    assert custom_content in result_name.stdout
    # Separator between default and custom
    assert result_name.stdout.count(SEPARATOR.strip()) == 1

    # Test loading by path '.pm/guidelines/my_custom.md'
    print("STDOUT (by path):", result_path.stdout)
    print("STDERR (by path):", result_path.stderr)
    assert result_path.exit_code == 0
    assert result_path.stderr == ""
    assert DEFAULT_CONTENT_SNIPPET in result_path.stdout  # Default is included
    assert custom_content in result_path.stdout
    # Separator between default and custom
    assert result_path.stdout.count(SEPARATOR.strip()) == 1

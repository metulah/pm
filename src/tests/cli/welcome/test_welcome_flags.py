# tests/cli/welcome/test_welcome_flags.py
from click.testing import CliRunner
from pathlib import Path

# Import the main cli entry point
from pm.cli.__main__ import cli

# Import constants and fixtures from conftest
from .conftest import (
    DEFAULT_CONTENT_SNIPPET,
    CODING_CONTENT_SNIPPET,
    VCS_CONTENT_SNIPPET,
    TESTING_CONTENT_SNIPPET,
    CUSTOM_FILE_CONTENT
)


def test_welcome_builtin_coding_collated(runner: CliRunner):
    """Test `pm welcome -g coding` shows default + coding (collated)."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['welcome', '--guidelines', 'coding'])
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        assert result.exit_code == 0
        # Expect default 'pm' AND 'coding' due to append behavior in isolated env
        assert DEFAULT_CONTENT_SNIPPET in result.stdout
        assert CODING_CONTENT_SNIPPET in result.stdout
        assert VCS_CONTENT_SNIPPET not in result.stdout
        assert TESTING_CONTENT_SNIPPET not in result.stdout
        assert CUSTOM_FILE_CONTENT not in result.stdout
        # Expect 1 separator ('pm' + 'coding')
        assert result.stdout.count("<<<--- GUIDELINE SEPARATOR --->>>") == 1
        assert result.stderr == ""


def test_welcome_builtin_vcs_collated(runner: CliRunner):
    """Test `pm welcome -g vcs` shows default + vcs (collated)."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['welcome', '--guidelines', 'vcs'])
        assert result.exit_code == 0
        # Expect default 'pm' AND 'vcs'
        assert DEFAULT_CONTENT_SNIPPET in result.stdout
        assert VCS_CONTENT_SNIPPET in result.stdout
        assert CODING_CONTENT_SNIPPET not in result.stdout
        assert TESTING_CONTENT_SNIPPET not in result.stdout
        # Expect 1 separator ('pm' + 'vcs')
        assert result.stdout.count("<<<--- GUIDELINE SEPARATOR --->>>") == 1
        assert result.stderr == ""


def test_welcome_builtin_testing_collated(runner: CliRunner):
    """Test `pm welcome -g testing` shows default + testing (collated)."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['welcome', '--guidelines', 'testing'])
        assert result.exit_code == 0
        # Expect default 'pm' AND 'testing'
        assert DEFAULT_CONTENT_SNIPPET in result.stdout
        assert TESTING_CONTENT_SNIPPET in result.stdout
        assert CODING_CONTENT_SNIPPET not in result.stdout
        assert VCS_CONTENT_SNIPPET not in result.stdout
        # Expect 1 separator ('pm' + 'testing')
        assert result.stdout.count("<<<--- GUIDELINE SEPARATOR --->>>") == 1
        assert result.stderr == ""


def test_welcome_custom_file_collated(runner: CliRunner, temp_guideline_file: Path):
    """Test `pm welcome -g @<path>` shows default + custom file (collated)."""
    # NOTE: This test assumes the implementation uses -g or --guidelines and @ prefix
    # It will FAIL until the welcome.py code is updated for collation
    with runner.isolated_filesystem():
        # Use absolute path for the temp file within isolated context
        abs_temp_path = temp_guideline_file.resolve()
        arg = f"@{abs_temp_path}"
        result = runner.invoke(cli, ['welcome', '--guidelines', arg])
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        assert result.exit_code == 0
        # Expect default 'pm' AND custom file content
        assert DEFAULT_CONTENT_SNIPPET in result.stdout
        assert CODING_CONTENT_SNIPPET not in result.stdout
        assert CUSTOM_FILE_CONTENT in result.stdout
        # Expect 1 separator ('pm' + custom file)
        assert result.stdout.count("<<<--- GUIDELINE SEPARATOR --->>>") == 1
        assert result.stderr == ""


def test_welcome_builtin_coding_and_file_collated(runner: CliRunner, temp_guideline_file: Path):
    """Test `pm welcome -g coding -g @<path>` shows default + coding + file (collated)."""
    with runner.isolated_filesystem():
        abs_temp_path = temp_guideline_file.resolve()
        arg = f"@{abs_temp_path}"
        result = runner.invoke(
            cli, ['welcome', '--guidelines', 'coding', '--guidelines', arg])
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        assert result.exit_code == 0
        # Expect default 'pm' + 'coding' + custom file
        assert DEFAULT_CONTENT_SNIPPET in result.stdout
        assert CODING_CONTENT_SNIPPET in result.stdout
        assert CUSTOM_FILE_CONTENT in result.stdout
        assert VCS_CONTENT_SNIPPET not in result.stdout
        # Expect 2 separators ('pm' + 'coding' + file)
        assert result.stdout.count("<<<--- GUIDELINE SEPARATOR --->>>") == 2
        assert result.stderr == ""


def test_welcome_all_builtins_collated(runner: CliRunner):
    """Test `pm welcome -g coding -g vcs -g testing` shows all."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['welcome', '--guidelines',
                               'coding', '--guidelines', 'vcs', '--guidelines', 'testing'])
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        assert result.exit_code == 0
        # Expect default 'pm' + 'coding' + 'vcs' + 'testing'
        assert DEFAULT_CONTENT_SNIPPET in result.stdout
        assert CODING_CONTENT_SNIPPET in result.stdout
        assert VCS_CONTENT_SNIPPET in result.stdout
        assert TESTING_CONTENT_SNIPPET in result.stdout
        assert CUSTOM_FILE_CONTENT not in result.stdout
        # Expect 3 separators ('pm' + 'coding' + 'vcs' + 'testing')
        assert result.stdout.count("<<<--- GUIDELINE SEPARATOR --->>>") == 3
        assert result.stderr == ""

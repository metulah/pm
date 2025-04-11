# tests/cli/welcome/test_welcome_flags.py
import pytest
from click.testing import CliRunner
from pathlib import Path
import os

# Import the main cli entry point
from pm.cli.__main__ import cli

# Import constants and fixtures from conftest
from .conftest import (
    DEFAULT_CONTENT_SNIPPET,
    CODING_CONTENT_SNIPPET,
    VCS_CONTENT_SNIPPET,
    TESTING_CONTENT_SNIPPET,
    CUSTOM_FILE_CONTENT,
    SEPARATOR,
    runner,  # Import fixtures if needed directly
    temp_guideline_file
)


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
    # Check for core separator text
    assert "<<<--- GUIDELINE SEPARATOR --->>>" in result.stdout
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
    # Check for core separator text
    assert "<<<--- GUIDELINE SEPARATOR --->>>" in result.stdout
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
    # Check for core separator text count
    assert result.stdout.count("<<<--- GUIDELINE SEPARATOR --->>>") == 2
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
    # Expect three separators (core text)
    assert result.stdout.count("<<<--- GUIDELINE SEPARATOR --->>>") == 3
    assert result.stderr == ""

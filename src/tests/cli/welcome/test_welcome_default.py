# tests/cli/welcome/test_welcome_default.py
from click.testing import CliRunner
from pathlib import Path
import os

# Import the main cli entry point
from pm.cli.__main__ import cli

# Import constants from conftest
from .conftest import (
    DEFAULT_CONTENT_SNIPPET,
    CODING_CONTENT_SNIPPET,
    VCS_CONTENT_SNIPPET,
    TESTING_CONTENT_SNIPPET,
    CUSTOM_FILE_CONTENT,
    SEPARATOR
)


def test_welcome_no_config(runner: CliRunner, tmp_path: Path):
    """Test `pm welcome` shows only 'pm' guideline when no config exists."""
    original_cwd = Path.cwd()
    os.chdir(tmp_path)  # Ensure we are in a clean directory
    try:
        result = runner.invoke(cli, ['welcome'])
    finally:
        os.chdir(original_cwd)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0
    assert DEFAULT_CONTENT_SNIPPET in result.stdout  # 'pm' guideline content
    assert CODING_CONTENT_SNIPPET not in result.stdout
    assert VCS_CONTENT_SNIPPET not in result.stdout
    assert TESTING_CONTENT_SNIPPET not in result.stdout
    assert CUSTOM_FILE_CONTENT not in result.stdout
    assert SEPARATOR not in result.stdout
    assert result.stderr == ""

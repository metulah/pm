# tests/cli/welcome/test_welcome_config.py
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
    SEPARATOR
)


def test_welcome_config_replaces_default(runner: CliRunner, temp_pm_dir: Path):
    """Test config's active list replaces the default 'pm' guideline."""
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["coding", "testing"]
"""
    config_path.write_text(config_content, encoding='utf-8')

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)  # chdir to tmp_path which contains .pm/
    try:
        result = runner.invoke(cli, ['welcome'])
    finally:
        os.chdir(original_cwd)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0
    assert DEFAULT_CONTENT_SNIPPET not in result.stdout  # 'pm' is NOT included
    assert CODING_CONTENT_SNIPPET in result.stdout
    assert TESTING_CONTENT_SNIPPET in result.stdout
    assert VCS_CONTENT_SNIPPET not in result.stdout
    # One separator between coding and testing
    assert result.stdout.count(SEPARATOR.strip()) == 1
    assert result.stderr == ""


def test_welcome_config_includes_default(runner: CliRunner, temp_pm_dir: Path):
    """Test config's active list can explicitly include the 'pm' guideline."""
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["pm", "vcs"]
"""
    config_path.write_text(config_content, encoding='utf-8')

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        result = runner.invoke(cli, ['welcome'])
    finally:
        os.chdir(original_cwd)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0
    assert DEFAULT_CONTENT_SNIPPET in result.stdout  # 'pm' IS included
    assert VCS_CONTENT_SNIPPET in result.stdout
    assert CODING_CONTENT_SNIPPET not in result.stdout
    # One separator between pm and vcs
    assert result.stdout.count(SEPARATOR.strip()) == 1
    assert result.stderr == ""


def test_welcome_config_custom_file_path(runner: CliRunner, temp_pm_dir: Path):
    """Test config loading a guideline via relative file path."""
    custom_guideline_rel_path = ".pm/guidelines/my_workflow.md"
    custom_guideline_abs_path = temp_pm_dir.parent / custom_guideline_rel_path
    custom_guideline_abs_path.parent.mkdir(parents=True, exist_ok=True)
    custom_guideline_abs_path.write_text(
        "Custom workflow step 1.", encoding='utf-8')

    config_path = temp_pm_dir / "config.toml"
    config_content = f"""
[guidelines]
active = ["coding", "{custom_guideline_rel_path}"]
"""
    config_path.write_text(config_content, encoding='utf-8')

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        result = runner.invoke(cli, ['welcome'])
    finally:
        os.chdir(original_cwd)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0
    assert CODING_CONTENT_SNIPPET in result.stdout
    # Check that the custom content IS loaded now
    assert "Custom workflow step 1." in result.stdout
    assert DEFAULT_CONTENT_SNIPPET not in result.stdout
    # Expect one separator between 'coding' and the custom guideline
    assert result.stdout.count(SEPARATOR.strip()) == 1
    assert result.stderr == ""  # Expect no warnings if loading succeeds


# Removed test_welcome_config_db_guideline as DB lookup is not implemented in welcome


def test_welcome_config_malformed_toml(runner: CliRunner, temp_pm_dir: Path):
    """Test fallback and warning with malformed TOML config."""
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["coding", "testing" # Missing closing quote and bracket
"""
    config_path.write_text(config_content, encoding='utf-8')

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        result = runner.invoke(cli, ['welcome'])
    finally:
        os.chdir(original_cwd)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0  # Should still succeed but show default
    assert DEFAULT_CONTENT_SNIPPET in result.stdout  # Fallback to 'pm'
    assert CODING_CONTENT_SNIPPET not in result.stdout
    assert SEPARATOR not in result.stdout
    assert "Warning: Error parsing .pm/config.toml" in result.stderr


def test_welcome_config_invalid_active_type(runner: CliRunner, temp_pm_dir: Path):
    """Test fallback and warning with invalid type for guidelines.active."""
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = "coding" # Should be a list
"""
    config_path.write_text(config_content, encoding='utf-8')

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        result = runner.invoke(cli, ['welcome'])
    finally:
        os.chdir(original_cwd)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0  # Should still succeed but show default
    assert DEFAULT_CONTENT_SNIPPET in result.stdout  # Fallback to 'pm'
    assert CODING_CONTENT_SNIPPET not in result.stdout
    assert SEPARATOR not in result.stdout
    assert "Warning: Invalid format for '[guidelines].active'" in result.stderr


def test_welcome_config_unresolvable_guideline(runner: CliRunner, temp_pm_dir: Path):
    """Test warning when a guideline in config cannot be resolved."""
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["coding", "nonexistent-guideline", "testing"]
"""
    config_path.write_text(config_content, encoding='utf-8')

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        # No need to patch DB lookup anymore as it's not used here
        result = runner.invoke(cli, ['welcome'])
    finally:
        os.chdir(original_cwd)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0  # Command succeeds, just skips the bad one
    assert CODING_CONTENT_SNIPPET in result.stdout
    assert TESTING_CONTENT_SNIPPET in result.stdout
    assert DEFAULT_CONTENT_SNIPPET not in result.stdout
    # Separator between coding and testing
    assert result.stdout.count(SEPARATOR.strip()) == 1
    # Check updated warning
    # Check updated warning
    assert "Warning: Could not find guideline source 'nonexistent-guideline' (Not found as built-in or custom file name)." in result.stderr


def test_welcome_config_and_cli_flag_additive(runner: CliRunner, temp_pm_dir: Path):
    """Test that -g flag adds to guidelines specified in config."""
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["coding"]
"""
    config_path.write_text(config_content, encoding='utf-8')

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        # Add 'testing' via flag
        result = runner.invoke(cli, ['welcome', '--guidelines', 'testing'])
    finally:
        os.chdir(original_cwd)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0
    assert CODING_CONTENT_SNIPPET in result.stdout  # From config
    assert TESTING_CONTENT_SNIPPET in result.stdout  # From flag
    assert DEFAULT_CONTENT_SNIPPET not in result.stdout
    assert result.stdout.count(SEPARATOR.strip()) == 1
    assert result.stderr == ""


def test_welcome_config_and_cli_flag_duplicate(runner: CliRunner, temp_pm_dir: Path):
    """Test that specifying the same guideline in config and -g shows it once."""
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["coding", "vcs"]
"""
    config_path.write_text(config_content, encoding='utf-8')

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        # Add 'coding' again via flag
        result = runner.invoke(cli, ['welcome', '--guidelines', 'coding'])
    finally:
        os.chdir(original_cwd)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0
    assert CODING_CONTENT_SNIPPET in result.stdout  # From config/flag
    assert VCS_CONTENT_SNIPPET in result.stdout  # From config
    assert DEFAULT_CONTENT_SNIPPET not in result.stdout
    # Should only appear once
    assert result.stdout.count(CODING_CONTENT_SNIPPET) == 1
    assert result.stdout.count(SEPARATOR.strip()) == 1  # Only one separator
    assert result.stderr == ""


def test_welcome_config_and_cli_flag_error(runner: CliRunner, temp_pm_dir: Path):
    """Test config guidelines show even if -g flag specifies an invalid one."""
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["coding"]
"""
    config_path.write_text(config_content, encoding='utf-8')

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        # Add 'nonexistent' via flag
        result = runner.invoke(cli, ['welcome', '--guidelines', 'nonexistent'])
    finally:
        os.chdir(original_cwd)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    # Command fails because an *explicitly requested* guideline failed
    assert result.exit_code == 1
    # No output should be generated on stdout when explicit error occurs
    assert result.stdout == ""
    # assert CODING_CONTENT_SNIPPET in result.stdout # From config - NO, stdout empty on error
    # assert DEFAULT_CONTENT_SNIPPET not in result.stdout
    # assert SEPARATOR not in result.stdout
    assert "Warning: Could not find guideline source 'nonexistent'" in result.stderr
    assert "Error: One or more specified guidelines could not be loaded." in result.stderr

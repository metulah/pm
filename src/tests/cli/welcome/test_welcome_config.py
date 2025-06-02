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
    SEPARATOR,
)


def test_welcome_config_replaces_default(runner: CliRunner, temp_pm_dir: Path):
    """
    Test that when a config file specifies active guidelines,
    it replaces the default 'pm' guideline with the specified ones.

    Verifies that:
    - Only the specified guidelines are displayed
    - The default guideline is not included
    - Proper separators are shown between guidelines
    - No errors are reported
    """
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["coding", "testing"]
"""
    config_path.write_text(config_content, encoding="utf-8")

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)  # chdir to tmp_path which contains .pm/
    try:
        result = runner.invoke(cli, ["welcome"])
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
    """
    Test that the config file can explicitly include the default 'pm' guideline
    along with other guidelines.

    Verifies that:
    - The default guideline is included when specified
    - Additional specified guidelines are included
    - Proper separators are shown between guidelines
    - No errors are reported
    """
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["pm", "vcs"]
"""
    config_path.write_text(config_content, encoding="utf-8")

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        result = runner.invoke(cli, ["welcome"])
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
    """
    Test that the config file can load guidelines specified via relative file paths.

    Verifies that:
    - Custom guidelines from relative paths are loaded correctly
    - Built-in guidelines are loaded correctly
    - Guidelines are combined with proper separators
    - No warnings or errors are reported
    """
    custom_guideline_rel_path = ".pm/guidelines/my_workflow.md"
    custom_guideline_abs_path = temp_pm_dir.parent / custom_guideline_rel_path
    custom_guideline_abs_path.parent.mkdir(parents=True, exist_ok=True)
    custom_guideline_abs_path.write_text("Custom workflow step 1.", encoding="utf-8")

    config_path = temp_pm_dir / "config.toml"
    config_content = f"""
[guidelines]
active = ["coding", "{custom_guideline_rel_path}"]
"""
    config_path.write_text(config_content, encoding="utf-8")

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        result = runner.invoke(cli, ["welcome"])
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


def test_welcome_config_malformed_toml(runner: CliRunner, temp_pm_dir: Path):
    """
    Test that when the config file contains malformed TOML,
    the system falls back to the default guideline and shows a warning.

    Verifies that:
    - Default guideline is shown when config is invalid
    - Invalid guideline names are ignored
    - A warning about the parsing error is shown
    - Command exits successfully
    """
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["invalid_guideline # Missing closing bracket and quote
"""
    config_path.write_text(config_content, encoding="utf-8")

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        result = runner.invoke(cli, ["welcome"])
    finally:
        os.chdir(original_cwd)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    assert result.exit_code == 0  # Should still succeed but show default
    assert DEFAULT_CONTENT_SNIPPET in result.stdout  # Fallback to 'pm'
    assert "invalid_guideline" not in result.stdout
    assert SEPARATOR not in result.stdout
    assert "Warning: Error parsing" in result.stderr


def test_welcome_config_invalid_active_type(runner: CliRunner, temp_pm_dir: Path):
    """
    Test that when the 'active' field in config has an invalid type (not a list),
    the system falls back to the default guideline and shows a warning.

    Verifies that:
    - Default guideline is shown when config is invalid
    - Specified guidelines are ignored
    - A warning about the invalid format is shown
    - Command exits successfully
    """
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = "coding" # Should be a list
"""
    config_path.write_text(config_content, encoding="utf-8")

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        result = runner.invoke(cli, ["welcome"])
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
    """
    Test that when the config file contains unresolvable guideline names,
    they are skipped with a warning but valid guidelines are still shown.

    Verifies that:
    - Valid guidelines are displayed
    - Unresolvable guidelines are skipped with a warning
    - Command exits successfully
    - Proper separators are shown between valid guidelines
    """
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["coding", "nonexistent-guideline", "testing"]
"""
    config_path.write_text(config_content, encoding="utf-8")

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        # No need to patch DB lookup anymore as it's not used here
        result = runner.invoke(cli, ["welcome"])
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
    assert (
        "Warning: Could not find guideline source 'nonexistent-guideline' (Not found as built-in or custom file name)."
        in result.stderr
    )


def test_welcome_config_and_cli_flag_additive(runner: CliRunner, temp_pm_dir: Path):
    """
    Test that guidelines specified via CLI flags are additive to those in config.

    Verifies that:
    - Guidelines from both config and CLI flags are combined
    - All specified guidelines are shown
    - Proper separators are shown between guidelines
    - No errors are reported
    """
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["coding"]
"""
    config_path.write_text(config_content, encoding="utf-8")

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        # Add 'testing' via flag
        result = runner.invoke(cli, ["welcome", "--guidelines", "testing"])
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
    """
    Test that duplicate guideline specifications (in config and CLI)
    result in the guideline being shown only once.

    Verifies that:
    - Guidelines are deduplicated
    - Each unique guideline is shown exactly once
    - Proper separators are shown between guidelines
    - No errors are reported
    """
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["coding", "vcs"]
"""
    config_path.write_text(config_content, encoding="utf-8")

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        # Add 'coding' again via flag
        result = runner.invoke(cli, ["welcome", "--guidelines", "coding"])
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
    """
    Test that when CLI flags specify an invalid guideline,
    the command fails but config-specified guidelines are not shown.

    Verifies that:
    - Command exits with error code 1
    - Config-specified guidelines are not shown
    - Error message about failed guideline loading is shown
    - Warning about the invalid guideline is shown
    """
    config_path = temp_pm_dir / "config.toml"
    config_content = """
[guidelines]
active = ["coding"]
"""
    config_path.write_text(config_content, encoding="utf-8")

    original_cwd = Path.cwd()
    os.chdir(temp_pm_dir.parent)
    try:
        # Add 'nonexistent' via flag
        result = runner.invoke(cli, ["welcome", "--guidelines", "nonexistent"])
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
    assert (
        "Error: One or more specified guidelines could not be loaded." in result.stderr
    )

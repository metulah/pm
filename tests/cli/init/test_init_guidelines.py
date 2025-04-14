# tests/cli/init/test_init_guidelines.py
import pytest
import tomllib
from pathlib import Path
from click.testing import CliRunner

# Import the main cli entry point
from pm.cli.base import cli

# Define expected paths and messages (copied from original)
PM_DIR_NAME = ".pm"
SUCCESS_MSG_SNIPPET = "Successfully initialized pm database"


# --- Fixtures ---

@pytest.fixture(scope="module")
def runner():
    """Provides a Click CliRunner with separated stderr."""
    # mix_stderr=False is important to capture stderr separately for errors
    return CliRunner(mix_stderr=False)


# --- Guideline Selection Tests ---

def test_init_interactive_default_guideline_selection(runner: CliRunner):
    """Test `pm init` interactive, accepting default guideline selection."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        # Input: \n for initial confirmation, \n for default guideline selection
        result = runner.invoke(
            cli, ['init'], input='\n\n', catch_exceptions=False)

        print("STDOUT (interactive default guideline):", result.stdout)
        print("STDERR (interactive default guideline):", result.stderr)

        assert result.exit_code == 0, f"CLI Error: {result.stderr or result.stdout}"
        assert result.stderr == ""
        assert SUCCESS_MSG_SNIPPET in result.stdout
        # Check for guideline prompt elements
        assert "Available guidelines" in result.stdout
        assert "Enter slugs of guidelines to activate" in result.stdout
        # Check default message
        assert "Applying default guideline 'pm'." in result.stdout  # Check default message

        # Verify config file creation and content
        config_path = fs_path / PM_DIR_NAME / "config.toml"
        assert config_path.is_file(), f"Config file not found at {config_path}"

        config_content = ""  # Initialize in case read fails
        try:
            config_content = config_path.read_text()
            config_data = tomllib.loads(config_content)
        except Exception as e:
            pytest.fail(
                f"Failed to read or parse {config_path}: {e}\nContent:\n{config_content}")

        assert "guidelines" in config_data, f"Config missing [guidelines] section in:\n{config_content}"
        assert "active" in config_data.get(
            "guidelines", {}), f"Config missing [guidelines].active key in:\n{config_content}"
        assert config_data["guidelines"]["active"] == [
            "pm"], f"Default guideline 'pm' not set correctly in:\n{config_content}"


def test_init_interactive_specific_guideline_selection(runner: CliRunner):
    """Test `pm init` interactive, selecting specific guidelines."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        # Input: \n for initial confirmation, coding,vcs\n for specific selection
        input_str = '\ncoding, vcs\n'  # Add space for realism, should be stripped
        result = runner.invoke(
            cli, ['init'], input=input_str, catch_exceptions=False)

        print("STDOUT (interactive specific guideline):", result.stdout)
        print("STDERR (interactive specific guideline):", result.stderr)

        assert result.exit_code == 0, f"CLI Error: {result.stderr or result.stdout}"
        assert result.stderr == ""
        assert SUCCESS_MSG_SNIPPET in result.stdout
        # Check for guideline prompt elements
        assert "Available guidelines" in result.stdout
        assert "Enter slugs of guidelines to activate" in result.stdout
        # Check the confirmation message for the specific selection
        assert "Set active guidelines to: ['coding', 'vcs']" in result.stdout

        # Verify config file creation and content
        config_path = fs_path / PM_DIR_NAME / "config.toml"
        assert config_path.is_file(), f"Config file not found at {config_path}"

        config_content = ""  # Initialize in case read fails
        try:
            config_content = config_path.read_text()
            config_data = tomllib.loads(config_content)
        except Exception as e:
            pytest.fail(
                f"Failed to read or parse {config_path}: {e}\nContent:\n{config_content}")

        assert "guidelines" in config_data, f"Config missing [guidelines] section in:\n{config_content}"
        assert "active" in config_data.get(
            "guidelines", {}), f"Config missing [guidelines].active key in:\n{config_content}"
        # Check for the specific selected guidelines, order preserved
        assert config_data["guidelines"]["active"] == [
            "coding", "vcs"], f"Specific guidelines not set correctly in:\n{config_content}"


def test_init_interactive_rerun_keep_selection(runner: CliRunner):
    """Test `pm init` interactive re-run, keeping existing guideline selection."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        initial_guidelines = ['coding', 'vcs']
        initial_guidelines_str = ','.join(initial_guidelines)

        # First run: Set specific guidelines
        input1 = f'\n{initial_guidelines_str}\n'
        result1 = runner.invoke(
            cli, ['init'], input=input1, catch_exceptions=False)
        assert result1.exit_code == 0, "First init run failed"
        config_path = fs_path / PM_DIR_NAME / "config.toml"
        assert config_path.is_file(), "Config file not created on first run"
        try:
            config_data1 = tomllib.loads(config_path.read_text())
            assert config_data1["guidelines"]["active"] == initial_guidelines
        except Exception as e:
            pytest.fail(f"Failed to verify config after first run: {e}")

        # Second run: Re-run interactively, press Enter to keep selection
        # Input: \n for initial confirmation (not needed on re-run), \n for guideline prompt
        input2 = '\n'  # Only need input for guideline prompt on re-run
        result2 = runner.invoke(
            cli, ['init'], input=input2, catch_exceptions=False)

        print("STDOUT (interactive rerun keep):", result2.stdout)
        print("STDERR (interactive rerun keep):", result2.stderr)

        assert result2.exit_code == 0, f"CLI Error on re-run: {result2.stderr or result2.stdout}"
        assert result2.stderr == ""
        assert "PM database already exists" in result2.stdout  # Check re-run message
        assert "Keeping current guideline selection." in result2.stdout  # Check keep message

        # Verify config file content is unchanged
        try:
            config_content2 = config_path.read_text()
            config_data2 = tomllib.loads(config_content2)
        except Exception as e:
            pytest.fail(
                f"Failed to read or parse config on re-run: {e}\nContent:\n{config_content2}")

        assert config_data2["guidelines"][
            "active"] == initial_guidelines, f"Guidelines changed unexpectedly on re-run:\n{config_content2}"


def test_init_interactive_rerun_change_selection(runner: CliRunner):
    """Test `pm init` interactive re-run, changing guideline selection."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        initial_guidelines = ['coding', 'vcs']
        initial_guidelines_str = ','.join(initial_guidelines)
        new_guidelines = ['testing', 'pm']
        new_guidelines_str = ','.join(new_guidelines)

        # First run: Set initial guidelines
        input1 = f'\n{initial_guidelines_str}\n'
        result1 = runner.invoke(
            cli, ['init'], input=input1, catch_exceptions=False)
        assert result1.exit_code == 0, "First init run failed"
        config_path = fs_path / PM_DIR_NAME / "config.toml"
        assert config_path.is_file(), "Config file not created on first run"

        # Second run: Re-run interactively, enter new guidelines
        # Input: \n for initial confirmation (not needed), new_guidelines_str\n for prompt
        # Only need input for guideline prompt
        input2 = f'{new_guidelines_str}\n'
        result2 = runner.invoke(
            cli, ['init'], input=input2, catch_exceptions=False)

        print("STDOUT (interactive rerun change):", result2.stdout)
        print("STDERR (interactive rerun change):", result2.stderr)

        assert result2.exit_code == 0, f"CLI Error on re-run: {result2.stderr or result2.stdout}"
        assert result2.stderr == ""
        assert "PM database already exists" in result2.stdout  # Check re-run message
        # Check change message
        assert f"Set active guidelines to: {new_guidelines}" in result2.stdout

        # Verify config file content is updated
        config_content2 = ""
        try:
            config_content2 = config_path.read_text()
            config_data2 = tomllib.loads(config_content2)
        except Exception as e:
            pytest.fail(
                f"Failed to read or parse config on re-run: {e}\nContent:\n{config_content2}")

        assert config_data2["guidelines"][
            "active"] == new_guidelines, f"Guidelines not updated correctly on re-run:\n{config_content2}"


def test_init_non_interactive_first_run_guidelines(runner: CliRunner):
    """Test `pm init -y` creates config with default guidelines on first run."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        result = runner.invoke(cli, ['init', '-y'], catch_exceptions=False)

        print("STDOUT (non-interactive first run guidelines):", result.stdout)
        print("STDERR (non-interactive first run guidelines):", result.stderr)

        assert result.exit_code == 0, f"CLI Error: {result.stderr or result.stdout}"
        assert result.stderr == ""
        assert "Set default active guidelines: ['pm']" in result.stdout

        # Verify config file creation and content
        config_path = fs_path / PM_DIR_NAME / "config.toml"
        assert config_path.is_file(), f"Config file not found at {config_path}"

        config_content = ""
        try:
            config_content = config_path.read_text()
            config_data = tomllib.loads(config_content)
        except Exception as e:
            pytest.fail(
                f"Failed to read or parse {config_path}: {e}\nContent:\n{config_content}")

        assert config_data.get("guidelines", {}).get("active") == [
            "pm"], f"Default guideline 'pm' not set correctly in:\n{config_content}"


def test_init_non_interactive_rerun_guidelines(runner: CliRunner):
    """Test `pm init -y` does not change existing config on re-run."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        initial_guidelines = ['coding', 'testing']  # Use non-default
        initial_guidelines_str = ','.join(initial_guidelines)

        # First run: Set specific guidelines interactively
        input1 = f'\n{initial_guidelines_str}\n'
        result1 = runner.invoke(
            cli, ['init'], input=input1, catch_exceptions=False)
        assert result1.exit_code == 0, "First init run failed"
        config_path = fs_path / PM_DIR_NAME / "config.toml"
        assert config_path.is_file(), "Config file not created on first run"
        # Quick check it was set correctly
        try:
            config_data1 = tomllib.loads(config_path.read_text())
            assert config_data1["guidelines"]["active"] == initial_guidelines
        except Exception as e:
            pytest.fail(f"Failed to verify config after first run: {e}")

        # Second run: Non-interactive re-run
        result2 = runner.invoke(cli, ['init', '-y'], catch_exceptions=False)

        print("STDOUT (non-interactive rerun guidelines):", result2.stdout)
        print("STDERR (non-interactive rerun guidelines):", result2.stderr)

        assert result2.exit_code == 0, f"CLI Error on re-run: {result2.stderr or result2.stdout}"
        assert result2.stderr == ""
        assert "PM database already exists" in result2.stdout  # Check re-run message
        # Check the specific message for skipping config
        assert "Skipping guideline configuration in non-interactive re-run." in result2.stdout

        # Verify config file content is UNCHANGED
        config_content2 = ""
        try:
            config_content2 = config_path.read_text()
            config_data2 = tomllib.loads(config_content2)
        except Exception as e:
            pytest.fail(
                f"Failed to read or parse config on re-run: {e}\nContent:\n{config_content2}")

        assert config_data2["guidelines"][
            "active"] == initial_guidelines, f"Guidelines changed unexpectedly on non-interactive re-run:\n{config_content2}"

# tests/test_cli_guideline.py
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
import frontmatter  # Keep for potential error mocking

# Import the main cli entry point
from pm.cli import cli

# Define resources path relative to this test file, similar to test_cli_welcome.py
# tests/ -> ../ -> pm/ -> pm/resources/
RESOURCES_DIR = Path(__file__).parent.parent / 'pm' / 'resources'

# No need for mocked content, we'll test against actual files/output


@pytest.fixture
def runner():
    return CliRunner()


# Remove mocking for standard success case - test against actual output
def test_guideline_list_success(runner):
    """Test `pm guideline list` successfully lists actual guidelines."""
    # Use isolated filesystem to ensure no custom guidelines interfere
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['guideline', 'list'])

        assert result.exit_code == 0
        assert "Scanning for guidelines..." in result.output
        assert "Available Guidelines:" in result.output
        # Check against actual descriptions from files (adjust if they change)
        assert "- coding [Built-in]: Standards and conventions for writing code within this project." in result.output
        assert "- default [Built-in]: General usage guidelines, core commands, and session workflow for the PM tool." in result.output
        assert "- testing [Built-in]: Best practices for writing and maintaining tests for the project." in result.output
        assert "- vcs [Built-in]: Guidelines for using version control (Git), including branching and commit strategies." in result.output


# Keep mocking for the 'no guidelines found' edge case
# Patch the constant used within guideline.py
@patch('pm.cli.guideline.RESOURCES_DIR')
# Patch Path.cwd used within list_guidelines
@patch('pm.cli.guideline.Path.cwd')
def test_guideline_list_no_guidelines(mock_cwd, mock_resources_dir, runner):
    """Test `pm guideline list` when no guideline files are found."""
    # Mock the glob method for built-in dir
    mock_resources_dir.glob.return_value = []
    # Mock the glob method for custom dir (via mocked cwd)
    # Configure the mock object returned by cwd()
    mock_cwd_instance = mock_cwd.return_value
    mock_custom_dir = mock_cwd_instance / ".pm" / "guidelines"
    mock_custom_dir.glob.return_value = []  # No custom files

    result = runner.invoke(cli, ['guideline', 'list'])

    assert result.exit_code == 0
    assert "Scanning for guidelines..." in result.output
    # Message changed in implementation
    assert "No guidelines found." in result.output
    # Ensure the header isn't printed
    assert "Available Guidelines:" not in result.output


# Keep mocking for the 'no description' edge case
@patch('pm.cli.guideline.RESOURCES_DIR')
@patch('pm.cli.guideline.Path.cwd')  # Patch Path.cwd
def test_guideline_list_no_description(mock_cwd, mock_resources_dir, runner):
    """Test `pm guideline list` when a file has no description metadata."""
    mock_no_desc_path = MagicMock(spec=Path)
    mock_no_desc_path.name = 'welcome_guidelines_nodesc.md'
    mock_no_desc_path.is_file.return_value = True
    mock_resources_dir.glob.return_value = [mock_no_desc_path]
    # Mock custom dir glob to be empty
    mock_cwd.return_value.glob.return_value = []

    # Mock frontmatter.load specifically for this test
    def mock_load_side_effect(path_arg):
        post = frontmatter.Post(content="")  # Create a dummy post object
        if path_arg == mock_no_desc_path:
            # Simulate metadata without 'description' key
            post.metadata = {'title': 'No Description Here'}
        else:
            # This mock should only be called for the built-in file
            pytest.fail(f"Unexpected call to frontmatter.load with {path_arg}")
        return post

    # Patch frontmatter.load within the guideline module's scope
    with patch('pm.cli.guideline.frontmatter.load', side_effect=mock_load_side_effect):
        result = runner.invoke(cli, ['guideline', 'list'])

        assert result.exit_code == 0
        assert "Available Guidelines:" in result.output
        # Check default text and marker
        assert "- nodesc [Built-in]: No description available." in result.output


# Keep mocking for parsing error case
@patch('pm.cli.guideline.RESOURCES_DIR')
@patch('pm.cli.guideline.Path.cwd')  # Patch Path.cwd
def test_guideline_list_parsing_error(mock_cwd, mock_resources_dir, runner):
    """Test `pm guideline list` when frontmatter parsing fails for a file."""
    mock_invalid_path = MagicMock(spec=Path)
    mock_invalid_path.name = 'welcome_guidelines_invalid.md'
    mock_invalid_path.is_file.return_value = True
    mock_resources_dir.glob.return_value = [mock_invalid_path]
    # Mock custom dir glob to be empty
    mock_cwd.return_value.glob.return_value = []

    # Simulate frontmatter.load raising an exception
    mock_exception = Exception("Mock parsing error")
    with patch('pm.cli.guideline.frontmatter.load', side_effect=mock_exception):
        result = runner.invoke(cli, ['guideline', 'list'])

        assert result.exit_code == 0  # Command should still succeed overall
        # Check that the warning is printed, including the exception message
        expected_warning = f"[yellow]Warning:[/yellow] Could not parse metadata from built-in {mock_invalid_path.name}: {mock_exception}"
        # Use partial match as rich might add extra formatting/newlines
        assert "Could not parse metadata from built-in welcome_guidelines_invalid.md" in result.output
        assert "Mock parsing error" in result.output
        # Check that no guidelines list is printed if only errors occurred
        assert "Available Guidelines:" not in result.output
        assert "No guidelines found." in result.output  # Message changed


# Keep mocking for mixed success/error case
@patch('pm.cli.guideline.RESOURCES_DIR')
@patch('pm.cli.guideline.Path.cwd')  # Patch Path.cwd
def test_guideline_list_mixed_success_and_error(mock_cwd, mock_resources_dir, runner):
    """Test `pm guideline list` with one valid file and one parsing error."""
    mock_default_path = MagicMock(spec=Path)
    mock_default_path.name = 'welcome_guidelines_default.md'
    mock_default_path.is_file.return_value = True

    mock_invalid_path = MagicMock(spec=Path)
    mock_invalid_path.name = 'welcome_guidelines_invalid.md'
    mock_invalid_path.is_file.return_value = True

    mock_resources_dir.glob.return_value = [
        mock_default_path, mock_invalid_path]
    # Mock custom dir glob to be empty
    mock_cwd.return_value.glob.return_value = []

    # Mock frontmatter.load: succeed for default, fail for invalid
    mock_exception = Exception(
        "Mock YAML parsing error")  # Use generic Exception

    def mock_load_side_effect(path_arg):
        if path_arg == mock_default_path:
            post = frontmatter.Post(content="")
            post.metadata = {'description': 'Mock Default Description'}
            return post
        elif path_arg == mock_invalid_path:
            raise mock_exception
        else:
            # This mock should only be called for the built-in files
            pytest.fail(f"Unexpected call to frontmatter.load with {path_arg}")

    with patch('pm.cli.guideline.frontmatter.load', side_effect=mock_load_side_effect):
        result = runner.invoke(cli, ['guideline', 'list'])

        assert result.exit_code == 0
        # Check warning for the invalid file, including exception message
        expected_warning = f"[yellow]Warning:[/yellow] Could not parse metadata from built-in {mock_invalid_path.name}: {mock_exception}"
        assert "Could not parse metadata from built-in welcome_guidelines_invalid.md" in result.output
        assert "Mock YAML parsing error" in result.output
        # Check the header is present because one file succeeded
        assert "Available Guidelines:" in result.output
        # Check the valid one is listed with its mocked description and marker
        assert "- default [Built-in]: Mock Default Description" in result.output
        # Check the invalid one is NOT listed
        # Check just the name part isn't present
        assert "- invalid" not in result.output


# --- Tests for `pm guideline show` ---

def test_guideline_show_success(runner):
    """Test `pm guideline show <name>` successfully displays a built-in guideline."""
    # Use isolated filesystem to ensure no custom guidelines interfere
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['guideline', 'show', 'default'])

        assert result.exit_code == 0
        # Check for key content expected from welcome_guidelines_default.md
        # Note: Output is rendered by rich.markdown, not raw Markdown.
        assert "Displaying Built-in Guideline: default" in result.output  # Check header
        assert "Welcome to the PM Tool!" in result.output
        assert "Core Commands" in result.output
        assert "Session Workflow" in result.output
        # Check it doesn't include frontmatter
        assert "description:" not in result.output


def test_guideline_show_not_found(runner):
    """Test `pm guideline show <name>` when the guideline does not exist (built-in)."""
    # Use isolated filesystem to ensure no custom guidelines interfere
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['guideline', 'show', 'nonexistent'])

        assert result.exit_code != 0  # Expect non-zero exit code for error
        assert "Error: Guideline 'nonexistent' not found." in result.output  # Added period

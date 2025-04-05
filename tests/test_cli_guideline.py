# tests/test_cli_guideline.py
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
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
    result = runner.invoke(cli, ['guideline', 'list'])

    assert result.exit_code == 0
    assert "Scanning for guidelines..." in result.output
    assert "Available Guidelines:" in result.output
    # Check against actual descriptions from files (adjust if they change)
    assert "- coding: Standards and conventions for writing code within this project." in result.output
    assert "- default: General usage guidelines, core commands, and session workflow for the PM tool." in result.output
    assert "- testing: Best practices for writing and maintaining tests for the project." in result.output
    assert "- vcs: Guidelines for using version control (Git), including branching and commit strategies." in result.output


# Keep mocking for the 'no guidelines found' edge case
# Patch the constant used within guideline.py
@patch('pm.cli.guideline.RESOURCES_DIR')
def test_guideline_list_no_guidelines(mock_resources_dir, runner):
    """Test `pm guideline list` when no guideline files are found."""
    # Mock the glob method directly on the mocked RESOURCES_DIR object
    mock_resources_dir.glob.return_value = []  # Simulate no files found

    result = runner.invoke(cli, ['guideline', 'list'])

    assert result.exit_code == 0
    assert "Scanning for guidelines..." in result.output
    assert "No built-in guidelines found." in result.output
    # Ensure the header isn't printed
    assert "Available Guidelines:" not in result.output


# Keep mocking for the 'no description' edge case
@patch('pm.cli.guideline.RESOURCES_DIR')
def test_guideline_list_no_description(mock_resources_dir, runner):
    """Test `pm guideline list` when a file has no description metadata."""
    mock_no_desc_path = MagicMock(
        spec=Path)  # Use spec=Path for better mocking
    mock_no_desc_path.name = 'welcome_guidelines_nodesc.md'
    mock_no_desc_path.is_file.return_value = True

    mock_resources_dir.glob.return_value = [mock_no_desc_path]

    # Mock frontmatter.load specifically for this test
    def mock_load_side_effect(path_arg):
        post = frontmatter.Post(content="")  # Create a dummy post object
        if path_arg == mock_no_desc_path:
            # Simulate metadata without 'description' key
            post.metadata = {'title': 'No Description Here'}
        else:
            pytest.fail(f"Unexpected call to frontmatter.load with {path_arg}")
        return post

    # Patch frontmatter.load within the guideline module's scope
    with patch('pm.cli.guideline.frontmatter.load', side_effect=mock_load_side_effect):
        result = runner.invoke(cli, ['guideline', 'list'])

        assert result.exit_code == 0
        assert "Available Guidelines:" in result.output
        assert "- nodesc: No description available." in result.output  # Check default text


# Keep mocking for parsing error case
@patch('pm.cli.guideline.RESOURCES_DIR')
def test_guideline_list_parsing_error(mock_resources_dir, runner):
    """Test `pm guideline list` when frontmatter parsing fails for a file."""
    mock_invalid_path = MagicMock(spec=Path)
    mock_invalid_path.name = 'welcome_guidelines_invalid.md'
    mock_invalid_path.is_file.return_value = True

    mock_resources_dir.glob.return_value = [mock_invalid_path]

    # Simulate frontmatter.load raising an exception
    with patch('pm.cli.guideline.frontmatter.load', side_effect=Exception("Mock parsing error")):  # Use generic Exception
        result = runner.invoke(cli, ['guideline', 'list'])

        assert result.exit_code == 0  # Command should still succeed overall
        # Check that the warning is printed
        assert "Warning: Could not parse metadata from welcome_guidelines_invalid.md" in result.output
        # Check that no guidelines list is printed if only errors occurred
        assert "Available Guidelines:" not in result.output
        assert "No built-in guidelines found." in result.output  # Expect this message now


# Keep mocking for mixed success/error case
@patch('pm.cli.guideline.RESOURCES_DIR')
def test_guideline_list_mixed_success_and_error(mock_resources_dir, runner):
    """Test `pm guideline list` with one valid file and one parsing error."""
    mock_default_path = MagicMock(spec=Path)
    mock_default_path.name = 'welcome_guidelines_default.md'
    mock_default_path.is_file.return_value = True

    mock_invalid_path = MagicMock(spec=Path)
    mock_invalid_path.name = 'welcome_guidelines_invalid.md'
    mock_invalid_path.is_file.return_value = True

    mock_resources_dir.glob.return_value = [
        mock_default_path, mock_invalid_path]

    # Mock frontmatter.load: succeed for default, fail for invalid
    def mock_load_side_effect(path_arg):
        if path_arg == mock_default_path:
            post = frontmatter.Post(content="")
            post.metadata = {'description': 'Mock Default Description'}
            return post
        elif path_arg == mock_invalid_path:
            raise frontmatter.YAMLParseException("Mock YAML parsing error")
        else:
            pytest.fail(f"Unexpected call to frontmatter.load with {path_arg}")

    with patch('pm.cli.guideline.frontmatter.load', side_effect=mock_load_side_effect):
        result = runner.invoke(cli, ['guideline', 'list'])

        assert result.exit_code == 0
        # Check warning for the invalid file
        assert "Warning: Could not parse metadata from welcome_guidelines_invalid.md" in result.output
        # Check the header is present because one file succeeded
        assert "Available Guidelines:" in result.output
        # Check the valid one is listed with its mocked description
        assert "- default: Mock Default Description" in result.output
        # Check the invalid one is NOT listed
        assert "- invalid:" not in result.output

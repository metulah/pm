# tests/cli/guideline/test_list.py
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
import frontmatter

# Import the main cli entry point
from pm.cli import cli

# Define resources path relative to this test file
# tests/cli/guideline/ -> ../../ -> pm/ -> pm/resources/
RESOURCES_DIR = Path(__file__).parent.parent.parent / 'pm' / 'resources'


@pytest.fixture
def runner():
    return CliRunner()


# --- Built-in Guideline Tests ---

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
        # Changed 'default' to 'pm'
        assert "- pm [Built-in]: General usage guidelines, core commands, and session workflow for the PM tool." in result.output
        assert "- testing [Built-in]: Best practices for writing and maintaining tests for the project." in result.output
        assert "- vcs [Built-in]: Guidelines for using version control (Git), including branching and commit strategies." in result.output


# Keep mocking for the 'no guidelines found' edge case
# Patch the constant used within the core guideline module
@patch('pm.core.guideline.RESOURCES_DIR')
# Patch find_project_root used within the core guideline module
@patch('pm.core.guideline.find_project_root')
def test_guideline_list_no_guidelines(mock_find_root, mock_resources_dir, runner):
    """Test `pm guideline list` when no guideline files are found."""
    # Mock the glob method for built-in dir
    mock_resources_dir.glob.return_value = []
    # Mock find_project_root to return None (no project found)
    mock_find_root.return_value = None

    result = runner.invoke(cli, ['guideline', 'list'])

    assert result.exit_code == 0
    assert "Scanning for guidelines..." in result.output
    # Message changed in implementation
    assert "No guidelines found." in result.output
    # Ensure the header isn't printed
    assert "Available Guidelines:" not in result.output


# Patch the constant used within the core guideline module
@patch('pm.core.guideline.RESOURCES_DIR')
# Patch find_project_root used within the core guideline module
@patch('pm.core.guideline.find_project_root')
def test_guideline_list_no_description(mock_find_root, mock_resources_dir, runner):
    """Test `pm guideline list` when a file has no description metadata."""
    mock_no_desc_path = MagicMock(spec=Path)
    mock_no_desc_path.name = 'welcome_guidelines_nodesc.md'
    mock_no_desc_path.is_file.return_value = True
    mock_resources_dir.glob.return_value = [mock_no_desc_path]
    # Mock find_project_root to return None (no project found)
    mock_find_root.return_value = None

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

    # Patch frontmatter.load within the core guideline module's scope
    with patch('pm.core.guideline.frontmatter.load', side_effect=mock_load_side_effect):
        result = runner.invoke(cli, ['guideline', 'list'])

        assert result.exit_code == 0
        assert "Available Guidelines:" in result.output
        # Check default text and marker
        assert "- nodesc [Built-in]: No description available." in result.output


# Patch the constant used within the core guideline module
@patch('pm.core.guideline.RESOURCES_DIR')
# Patch find_project_root used within the core guideline module
@patch('pm.core.guideline.find_project_root')
def test_guideline_list_parsing_error(mock_find_root, mock_resources_dir, runner):
    """Test `pm guideline list` when frontmatter parsing fails for a file."""
    mock_invalid_path = MagicMock(spec=Path)
    mock_invalid_path.name = 'welcome_guidelines_invalid.md'
    mock_invalid_path.is_file.return_value = True
    mock_resources_dir.glob.return_value = [mock_invalid_path]
    # Mock find_project_root to return None (no project found)
    mock_find_root.return_value = None

    # Simulate frontmatter.load raising an exception
    mock_exception = Exception("Mock parsing error")
    # Patch frontmatter.load within the core guideline module's scope
    with patch('pm.core.guideline.frontmatter.load', side_effect=mock_exception):
        result = runner.invoke(cli, ['guideline', 'list'])

        assert result.exit_code == 0  # Command should still succeed overall
        # Check that the warning is printed, including the exception message
        # Use partial match as rich might add extra formatting/newlines
        assert "Could not parse metadata from built-in welcome_guidelines_invalid.md" in result.output
        assert "Mock parsing error" in result.output
        # Check that no guidelines list is printed if only errors occurred
        assert "Available Guidelines:" not in result.output
        assert "No guidelines found." in result.output  # Message changed


# Patch the constant used within the core guideline module
@patch('pm.core.guideline.RESOURCES_DIR')
# Patch find_project_root used within the core guideline module
@patch('pm.core.guideline.find_project_root')
def test_guideline_list_mixed_success_and_error(mock_find_root, mock_resources_dir, runner):
    """Test `pm guideline list` with one valid file and one parsing error."""
    mock_default_path = MagicMock(spec=Path)
    mock_default_path.name = 'welcome_guidelines_default.md'
    mock_default_path.is_file.return_value = True

    mock_invalid_path = MagicMock(spec=Path)
    mock_invalid_path.name = 'welcome_guidelines_invalid.md'
    mock_invalid_path.is_file.return_value = True

    mock_resources_dir.glob.return_value = [
        mock_default_path, mock_invalid_path]
    # Mock find_project_root to return None (no project found)
    mock_find_root.return_value = None

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

    # Patch frontmatter.load within the core guideline module's scope
    with patch('pm.core.guideline.frontmatter.load', side_effect=mock_load_side_effect):
        result = runner.invoke(cli, ['guideline', 'list'])

        assert result.exit_code == 0
        # Check warning for the invalid file, including exception message
        assert "Could not parse metadata from built-in welcome_guidelines_invalid.md" in result.output
        assert "Mock YAML parsing error" in result.output
        # Check the header is present because one file succeeded
        assert "Available Guidelines:" in result.output
        # Check the valid one is listed with its mocked description and marker
        assert "- default [Built-in]: Mock Default Description" in result.output
        # Check the invalid one is NOT listed
        # Check just the name part isn't present
        assert "- invalid" not in result.output


# --- Custom Guideline List Tests ---

# Helper to create a dummy guideline file (can be moved to conftest.py later if needed)
def _create_guideline_file(fs_path, name, content, metadata=None):
    guideline_dir = fs_path / ".pm" / "guidelines"
    guideline_dir.mkdir(parents=True, exist_ok=True)
    file_path = guideline_dir / f"{name}.md"
    # Use the provided metadata dict directly
    post = frontmatter.Post(content=content, metadata=metadata or {})
    with open(file_path, 'w', encoding='utf-8') as f:
        # Use dumps to get string, then write to text file handle
        f.write(frontmatter.dumps(post))
    return file_path


def test_guideline_list_shows_custom(runner):
    """Test `pm guideline list` includes custom guidelines."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        # This call uses the corrected helper
        _create_guideline_file(
            fs_path, "my-list-test", "Content", {'description': 'Custom Desc'})
        result = runner.invoke(cli, ['guideline', 'list'])
        assert result.exit_code == 0
        assert "Available Guidelines:" in result.output
        # Implementation reads description correctly now
        assert "- my-list-test [Custom]: Custom Desc" in result.output
        # Also check a built-in one is still listed (use partial match for flexibility)
        # Changed 'default' to 'pm'
        assert "- pm [Built-in]: General usage guidelines" in result.output


def test_guideline_list_custom_overrides_builtin_name(runner):
    """Test `pm guideline list` shows custom description when name conflicts with built-in."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        # Create custom 'coding' guideline using corrected helper
        _create_guideline_file(
            fs_path, "coding", "My coding rules", {'description': 'Local Coding Rules'})
        result = runner.invoke(cli, ['guideline', 'list'])
        assert result.exit_code == 0
        # Should only list 'coding' once, as Custom, with correct description
        assert "- coding [Custom]: Local Coding Rules" in result.output
        # Make sure built-in isn't also listed by checking absence of its type marker
        assert "- coding [Built-in]:" not in result.output


def test_guideline_list_multiple_custom_and_builtin(runner):
    """Test listing a mix of custom and built-in guidelines."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        # Use corrected helper
        _create_guideline_file(fs_path, "alpha-custom",
                               "A", {'description': 'Alpha'})
        _create_guideline_file(fs_path, "zeta-custom",
                               "Z", {'description': 'Zeta'})
        _create_guideline_file(fs_path, "testing", "Local Tests", {
                               'description': 'Local Testing Rules'})

        result = runner.invoke(cli, ['guideline', 'list'])
        assert result.exit_code == 0
        output = result.output

        # Check custom ones have correct descriptions
        assert "- alpha-custom [Custom]: Alpha" in output
        assert "- zeta-custom [Custom]: Zeta" in output
        assert "- testing [Custom]: Local Testing Rules" in output

        # Check remaining built-in ones (default, coding, vcs)
        # Changed 'default' to 'pm'
        assert "- pm [Built-in]: General usage guidelines" in output
        assert "- coding [Built-in]: Standards and conventions" in output
        assert "- vcs [Built-in]: Guidelines for using version control" in output

        # Ensure overridden built-in 'testing' is not listed as built-in
        assert "- testing [Built-in]:" not in output

        # Check sorting (alpha-custom, coding, default, testing (custom), vcs, zeta-custom)
        assert output.find("alpha-custom") < output.find("coding")
        assert output.find("coding") < output.find(
            "pm")  # Changed 'default' to 'pm'
        assert output.find("default") < output.find("testing [Custom]")
        assert output.find("testing [Custom]") < output.find("vcs")
        assert output.find("vcs") < output.find("zeta-custom")


def test_guideline_list_only_custom(runner):
    """Test listing when only custom guidelines exist (mock away built-ins)."""
    mock_resources_dir = MagicMock(spec=Path)
    mock_resources_dir.glob.return_value = []  # Simulate no files found by glob

    # Patch RESOURCES_DIR within the core guideline module
    with patch('pm.core.guideline.RESOURCES_DIR', mock_resources_dir):
        with runner.isolated_filesystem() as fs:
            fs_path = Path(fs)
            # Use corrected helper
            _create_guideline_file(fs_path, "only-custom",
                                   "Content", {'description': 'Only'})
            result = runner.invoke(cli, ['guideline', 'list'])

            assert result.exit_code == 0
            # Check custom guideline has correct description
            assert "- only-custom [Custom]: Only" in result.output
            assert "[Built-in]" not in result.output
            # Verify the mocked glob was called as expected on the mock object
            mock_resources_dir.glob.assert_called_once_with(
                'welcome_guidelines_*.md')


def test_guideline_list_no_custom(runner):
    """Test listing when no custom guidelines exist (should match original list test)."""
    with runner.isolated_filesystem():  # No custom files created
        result = runner.invoke(cli, ['guideline', 'list'])
        assert result.exit_code == 0
        assert "[Custom]" not in result.output
        # Check for built-in ones
        # Changed 'default' to 'pm'
        assert "- pm [Built-in]: General usage guidelines" in result.output
        assert "- coding [Built-in]: Standards and conventions" in result.output
        assert "- testing [Built-in]: Best practices for writing" in result.output
        assert "- vcs [Built-in]: Guidelines for using version control" in result.output

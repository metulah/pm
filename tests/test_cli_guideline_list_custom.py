# tests/test_cli_guideline_list_custom.py
import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, MagicMock  # Keep this import
import frontmatter

# Import the main cli entry point
from pm.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


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
        assert "- default [Built-in]: General usage guidelines" in result.output


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
        assert "- default [Built-in]: General usage guidelines" in output
        assert "- coding [Built-in]: Standards and conventions" in output
        assert "- vcs [Built-in]: Guidelines for using version control" in output

        # Ensure overridden built-in 'testing' is not listed as built-in
        assert "- testing [Built-in]:" not in output

        # Check sorting (alpha-custom, coding, default, testing (custom), vcs, zeta-custom)
        assert output.find("alpha-custom") < output.find("coding")
        assert output.find("coding") < output.find("default")
        assert output.find("default") < output.find("testing [Custom]")
        assert output.find("testing [Custom]") < output.find("vcs")
        assert output.find("vcs") < output.find("zeta-custom")


def test_guideline_list_only_custom(runner):
    """Test listing when only custom guidelines exist (mock away built-ins)."""
    mock_resources_dir = MagicMock(spec=Path)
    mock_resources_dir.glob.return_value = []  # Simulate no files found by glob

    with patch('pm.cli.guideline.list.RESOURCES_DIR', mock_resources_dir):  # Target updated
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
        assert "- default [Built-in]: General usage guidelines" in result.output
        assert "- coding [Built-in]: Standards and conventions" in result.output
        assert "- testing [Built-in]: Best practices for writing" in result.output
        assert "- vcs [Built-in]: Guidelines for using version control" in result.output

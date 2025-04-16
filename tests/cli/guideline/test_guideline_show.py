# tests/cli/guideline/test_show.py
import pytest
from click.testing import CliRunner
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


# Helper to create a dummy guideline file (can be moved to conftest.py later if needed)
def _create_guideline_file(fs_path, name, content, metadata=None):
    guideline_dir = fs_path / ".pm" / "guidelines"
    guideline_dir.mkdir(parents=True, exist_ok=True)
    file_path = guideline_dir / f"{name}.md"
    # Use the provided metadata dict directly
    post = frontmatter.Post(content=content, metadata=metadata or {})
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post))  # Use dumps to get string, then write
    return file_path


# --- Built-in Guideline Show Tests ---

def test_guideline_show_success(runner):
    """Test `pm guideline show <name>` successfully displays a built-in guideline."""
    # Use isolated filesystem to ensure no custom guidelines interfere
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['guideline', 'show', 'pm'])  # Use 'pm'

        assert result.exit_code == 0
        # Check for key content expected from welcome_guidelines_default.md
        # Note: Output is rendered by rich.markdown, not raw Markdown.
        # Check header (changed 'default' to 'pm')
        assert "Displaying Built-in Guideline: pm" in result.output
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
        assert "Error: Guideline 'nonexistent' not found." in result.output


# --- Custom Guideline Show Tests ---

def test_guideline_show_custom(runner):
    """Test `pm guideline show` displays a custom guideline."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        _create_guideline_file(
            fs_path, "show-custom", "Custom **Show** Content", {'description': 'Show Desc'})
        result = runner.invoke(cli, ['guideline', 'show', 'show-custom'])
        assert result.exit_code == 0
        assert "Displaying Custom Guideline: show-custom" in result.output
        # Check for raw content (rich rendering removed)
        assert "Custom **Show** Content" in result.output
        # Ensure frontmatter isn't shown in content
        assert "description:" not in result.output
        assert "Show Desc" not in result.output


def test_guideline_show_prefers_custom_over_builtin(runner):
    """Test `pm guideline show` displays custom version when name conflicts with built-in."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        # Override 'default' built-in guideline
        _create_guideline_file(
            fs_path, "default", "My **Local** Default Content")
        result = runner.invoke(cli, ['guideline', 'show', 'default'])
        assert result.exit_code == 0
        assert "Displaying Custom Guideline: default" in result.output
        assert "My **Local** Default Content" in result.output
        # Ensure built-in content isn't shown
        assert "Welcome to the PM Tool!" not in result.output


def test_guideline_show_builtin_when_no_custom(runner):
    """Test `pm guideline show` displays built-in when no custom version exists."""
    with runner.isolated_filesystem():  # No custom files created
        # Use a known built-in
        result = runner.invoke(cli, ['guideline', 'show', 'coding'])
        assert result.exit_code == 0
        assert "Displaying Built-in Guideline: coding" in result.output
        # Check for content from actual built-in coding.md
        assert "Coding Practices" in result.output
        assert "Follow the project's coding standards." in result.output


def test_guideline_show_error_not_found_anywhere(runner):
    """Test `pm guideline show` when guideline exists neither as custom nor built-in."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ['guideline', 'show', 'completely-nonexistent'])
        assert result.exit_code != 0
        assert "Error: Guideline 'completely-nonexistent' not found." in result.output

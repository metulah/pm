# tests/test_cli_guideline_copy.py
import pytest
from click.testing import CliRunner
from pathlib import Path
import frontmatter

# Import the main cli entry point
from pm.cli import cli

# Define resources path relative to this test file
RESOURCES_DIR = Path(__file__).parent.parent / 'pm' / 'resources'


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


def test_guideline_copy_success_from_builtin(runner):
    """Test copying a built-in guideline."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        result = runner.invoke(
            cli, ['guideline', 'copy', 'pm', 'my-default-copy'])  # Use 'pm'

        assert result.exit_code == 0
        assert "Successfully copied 'pm' (Built-in) to custom guideline 'my-default-copy'" in result.output

        dest_path = fs_path / ".pm" / "guidelines" / "my-default-copy.md"
        assert dest_path.is_file()

        # Verify content is similar to original built-in (check a known phrase)
        post = frontmatter.load(dest_path)
        assert "Welcome to the PM Tool!" in post.content
        # Verify metadata (description) was copied correctly, expecting nesting
        assert 'metadata' in post.metadata
        assert isinstance(post.metadata['metadata'], dict)
        assert "General usage guidelines" in post.metadata['metadata'].get(
            'description', '')


def test_guideline_copy_success_from_custom(runner):
    """Test copying an existing custom guideline."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        # Create the source custom file correctly
        _create_guideline_file(
            fs_path, "source-custom", "Source Content", {'description': 'Source Desc'})

        result = runner.invoke(
            cli, ['guideline', 'copy', 'source-custom', 'dest-custom'])

        assert result.exit_code == 0
        assert "Successfully copied 'source-custom' (Custom) to custom guideline 'dest-custom'" in result.output

        dest_path = fs_path / ".pm" / "guidelines" / "dest-custom.md"
        assert dest_path.is_file()

        # Verify content and metadata match the source custom file, expecting nesting
        post = frontmatter.load(dest_path)
        assert post.content.strip() == "Source Content"
        assert post.metadata == {'metadata': {'description': 'Source Desc'}}


def test_guideline_copy_error_source_not_found(runner):
    """Test copying when the source guideline doesn't exist."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ['guideline', 'copy', 'nonexistent-source', 'wont-happen'])
        assert result.exit_code != 0
        assert "Error: Source guideline 'nonexistent-source' not found." in result.output


def test_guideline_copy_error_destination_exists(runner):
    """Test copying when the destination custom guideline already exists."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        # Create the destination file first using the corrected helper
        _create_guideline_file(fs_path, "existing-dest",
                               "Pre-existing content")

        # Attempt to copy 'default' (or any valid source) to the existing destination
        result = runner.invoke(
            cli, ['guideline', 'copy', 'pm', 'existing-dest'])  # Use 'pm'

        assert result.exit_code != 0
        assert "Error: Destination custom guideline 'existing-dest' already exists." in result.output

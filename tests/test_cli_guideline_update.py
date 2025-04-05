# tests/test_cli_guideline_update.py
import pytest
from click.testing import CliRunner
from pathlib import Path
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


def test_guideline_update_success_description(runner):
    """Test `pm guideline update <name> --description <new>`."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        file_path = _create_guideline_file(
            fs_path, "update-desc", "Content", {'description': 'Old Desc'})
        result = runner.invoke(
            cli, ['guideline', 'update', 'update-desc', '--description', 'New Desc'])
        assert result.exit_code == 0
        assert "Successfully updated custom guideline 'update-desc'" in result.output
        post = frontmatter.load(file_path)
        # Expect nested metadata after update
        assert post.metadata == {'metadata': {'description': 'New Desc'}}
        assert post.content.strip() == "Content"  # Content unchanged


def test_guideline_update_success_clear_description(runner):
    """Test `pm guideline update <name> --description ""`."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        file_path = _create_guideline_file(
            fs_path, "clear-desc", "Content", {'description': 'Old Desc'})
        result = runner.invoke(
            cli, ['guideline', 'update', 'clear-desc', '--description', ''])
        assert result.exit_code == 0
        post = frontmatter.load(file_path)
        # Expect nested empty metadata after clearing the only key
        assert post.metadata == {'metadata': {}}


def test_guideline_update_success_content_inline(runner):
    """Test `pm guideline update <name> --content <new_inline>`."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        file_path = _create_guideline_file(
            fs_path, "update-content", "Old", {'description': 'Desc'})
        result = runner.invoke(
            cli, ['guideline', 'update', 'update-content', '--content', 'New'])
        assert result.exit_code == 0
        post = frontmatter.load(file_path)
        assert post.content.strip() == "New"
        # Description should remain unchanged within the nested structure
        assert post.metadata == {'metadata': {'description': 'Desc'}}


def test_guideline_update_success_content_from_file(runner):
    """Test `pm guideline update <name> --content @<path>`."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        file_path = _create_guideline_file(
            fs_path, "update-file", "Old", {'other_meta': 'keep'})
        source_path = fs_path / "new_content.md"
        source_path.write_text("New from file")
        result = runner.invoke(
            cli, ['guideline', 'update', 'update-file', '--content', f'@{source_path}'])
        assert result.exit_code == 0
        post = frontmatter.load(file_path)
        assert post.content.strip() == "New from file"
        # Other metadata should be preserved within the nested structure
        assert post.metadata == {'metadata': {'other_meta': 'keep'}}


def test_guideline_update_success_both_desc_and_content(runner):
    """Test updating both description and content simultaneously."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        file_path = _create_guideline_file(
            fs_path, "update-both", "Old Content", {'description': 'Old Desc', 'extra': 'Keep Me'})
        result = runner.invoke(cli, ['guideline', 'update', 'update-both',
                               '--description', 'New Desc', '--content', 'New Content'])
        assert result.exit_code == 0
        post = frontmatter.load(file_path)
        # Expect updated description and preserved extra key within nested structure
        assert post.metadata == {'metadata': {
            'description': 'New Desc', 'extra': 'Keep Me'}}
        assert post.content.strip() == "New Content"


def test_guideline_update_error_not_found(runner):
    """Test `pm guideline update` when the custom guideline doesn't exist."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ['guideline', 'update', 'nonexistent-update', '--content', 'Wont work'])
        assert result.exit_code != 0
        assert "Error: Custom guideline 'nonexistent-update' not found" in result.output


def test_guideline_update_error_on_builtin(runner):
    """Test `pm guideline update` fails on a built-in guideline."""
    with runner.isolated_filesystem():
        # Attempt to update 'default', which is built-in
        result = runner.invoke(
            cli, ['guideline', 'update', 'default', '--description', 'Trying to update built-in'])
        assert result.exit_code != 0
        # The error message should indicate that the *custom* guideline wasn't found
        assert "Error: Custom guideline 'default' not found" in result.output


def test_guideline_update_error_content_file_not_found(runner):
    """Test `pm guideline update --content @<path>` when the source file doesn't exist."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        _create_guideline_file(fs_path, "update-bad-source", "Old")
        result = runner.invoke(cli, ['guideline', 'update', 'update-bad-source',
                               '--content', '@nonexistent_update_source.md'])
        assert result.exit_code != 0
        assert "Error reading content file: File specified by '@' not found" in result.output

# tests/test_cli_guideline_create.py
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


def test_guideline_create_success_inline(runner):
    """Test `pm guideline create <name> --content <inline>`."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        result = runner.invoke(
            cli, ['guideline', 'create', 'my-custom', '--content', 'This is **custom** content.'])
        assert result.exit_code == 0
        assert "Successfully created custom guideline 'my-custom'" in result.output
        expected_path = fs_path / ".pm" / "guidelines" / "my-custom.md"
        assert expected_path.is_file()
        post = frontmatter.load(expected_path)
        assert post.content.strip() == 'This is **custom** content.'
        # Expect nested empty metadata dict when none provided
        assert post.metadata == {'metadata': {}}


def test_guideline_create_success_from_file(runner):
    """Test `pm guideline create <name> --content @<path>`."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        # Create a source file
        source_content = "Content from file."
        source_path = fs_path / "source.md"
        source_path.write_text(source_content)

        result = runner.invoke(
            cli, ['guideline', 'create', 'from-file-guide', '--content', f'@{source_path}'])
        assert result.exit_code == 0
        assert "Successfully created custom guideline 'from-file-guide'" in result.output
        expected_path = fs_path / ".pm" / "guidelines" / "from-file-guide.md"
        assert expected_path.is_file()
        post = frontmatter.load(expected_path)
        assert post.content.strip() == source_content
        # Expect nested empty metadata dict when none provided
        assert post.metadata == {'metadata': {}}


def test_guideline_create_success_with_description(runner):
    """Test `pm guideline create <name> --content <inline> --description <desc>`."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        result = runner.invoke(cli, ['guideline', 'create', 'desc-guide',
                               '--content', 'ABC', '--description', 'My Description'])
        assert result.exit_code == 0
        assert "Successfully created custom guideline 'desc-guide'" in result.output
        expected_path = fs_path / ".pm" / "guidelines" / "desc-guide.md"
        assert expected_path.is_file()
        post = frontmatter.load(expected_path)
        assert post.content.strip() == 'ABC'
        # Expect description nested under 'metadata' key
        assert post.metadata == {'metadata': {'description': 'My Description'}}


def test_guideline_create_error_already_exists(runner):
    """Test `pm guideline create` when the custom guideline already exists."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        # This call to the helper should now work correctly
        _create_guideline_file(fs_path, "existing-guide", "Old content")
        result = runner.invoke(
            cli, ['guideline', 'create', 'existing-guide', '--content', 'New content'])
        assert result.exit_code != 0
        assert "Error: Custom guideline 'existing-guide' already exists" in result.output


def test_guideline_create_error_file_not_found(runner):
    """Test `pm guideline create --content @<path>` when the source file doesn't exist."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ['guideline', 'create', 'bad-source', '--content', '@nonexistent_file.md'])
        assert result.exit_code != 0
        assert "Error reading content file: File specified by '@' not found" in result.output

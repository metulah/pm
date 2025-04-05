# tests/test_cli_guideline_delete.py
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
        f.write(frontmatter.dumps(post))  # Use dumps to get string, then write
    return file_path


def test_guideline_delete_success(runner):
    """Test `pm guideline delete <name> --force`."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        file_path = _create_guideline_file(fs_path, "to-delete", "Content")
        assert file_path.is_file()  # Pre-check

        result = runner.invoke(
            cli, ['guideline', 'delete', 'to-delete', '--force'])

        assert result.exit_code == 0
        assert "Successfully deleted custom guideline 'to-delete'" in result.output
        assert not file_path.exists()  # Check file is actually deleted


def test_guideline_delete_error_missing_force(runner):
    """Test `pm guideline delete` fails without --force."""
    with runner.isolated_filesystem() as fs:
        fs_path = Path(fs)
        file_path = _create_guideline_file(
            fs_path, "no-force-delete", "Content")
        assert file_path.is_file()  # Pre-check

        result = runner.invoke(cli, ['guideline', 'delete', 'no-force-delete'])

        assert result.exit_code != 0
        assert "Error: Deleting 'no-force-delete' requires the --force flag." in result.output
        assert file_path.is_file()  # Check file still exists


def test_guideline_delete_error_not_found(runner):
    """Test `pm guideline delete` when the custom guideline doesn't exist."""
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ['guideline', 'delete', 'nonexistent-delete', '--force'])
        assert result.exit_code != 0
        assert "Error: Custom guideline 'nonexistent-delete' not found" in result.output


def test_guideline_delete_error_on_builtin(runner):
    """Test `pm guideline delete` fails on a built-in guideline."""
    with runner.isolated_filesystem():
        # Attempt to delete 'default', which is built-in
        result = runner.invoke(
            cli, ['guideline', 'delete', 'default', '--force'])
        assert result.exit_code != 0
        # The error message should indicate that the *custom* guideline wasn't found
        assert "Error: Custom guideline 'default' not found" in result.output

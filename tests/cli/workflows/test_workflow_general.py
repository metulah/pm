"""Tests for miscellaneous CLI command workflows and interactions."""

import pytest
import json
# Needed for direct DB checks in cascade tests (though cascades moved)
from pm.storage import init_db
from pm.cli import cli
from click.testing import CliRunner

# --- Fixture for CLI Runner and DB Path ---


@pytest.fixture
def cli_runner_env(tmp_path):
    """Fixture providing a CliRunner and a temporary db_path."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)  # Initialize the db file
    conn.close()  # Close initial connection
    runner = CliRunner(mix_stderr=False)  # Don't mix stdout/stderr
    return runner, db_path

# --- Workflow Tests ---


def test_cli_simple_messages(cli_runner_env):
    """Test text format output for simple success/error messages using slugs."""
    runner, db_path = cli_runner_env

    # Setup: Create a project
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Message Test Proj'])
    project_data = json.loads(result_proj.output)['data']
    project_slug = project_data['slug']

    # Test delete success message (Text format) using slug - REQUIRES --force now
    result_del_text = runner.invoke(
        # Add --force
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'delete', project_slug, '--force'])
    assert result_del_text.exit_code == 0
    # Check message uses identifier
    # Check stdout for success message
    assert f"Success: Project '{project_slug}' deleted" in result_del_text.output

    # Test delete error message (Text format) using non-existent slug
    result_del_err_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'delete', 'non-existent-slug'])
    # Expect non-zero exit because project resolver fails (UsageError)
    assert result_del_err_text.exit_code != 0
    # Check stderr for the "not found" message from the resolver
    assert "Error: Project not found with identifier: 'non-existent-slug'" in result_del_err_text.stderr

# (Other tests moved to specific workflow files)

"""Tests for project CLI commands."""

import pytest
import json
from pm.storage import init_db
from pm.cli import cli  # Import the main cli entry point
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

# --- CLI Tests ---


def test_cli_project_crud(cli_runner_env):
    """Test basic project create, list, show, update via CLI using slugs."""
    runner, db_path = cli_runner_env
    from pm.storage import list_projects  # For verification

    # Verify database is empty initially
    with init_db(db_path) as conn:
        assert len(list_projects(conn)) == 0

    # Test project creation (JSON default)
    result_create = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'CLI Project 1', '--description', 'Desc 1'])
    assert result_create.exit_code == 0, f"Output: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    assert response_create["data"]["name"] == "CLI Project 1"
    assert response_create["data"]["status"] == "ACTIVE"
    project_id_1 = response_create["data"]["id"]
    project_slug_1 = response_create["data"]["slug"]  # Get slug
    assert project_slug_1 == "cli-project-1"  # Verify expected slug

    # Test project listing (JSON default)
    result_list = runner.invoke(cli, ['--db-path', db_path, 'project', 'list'])
    assert result_list.exit_code == 0
    response_list = json.loads(result_list.output)
    assert response_list["status"] == "success"
    assert len(response_list["data"]) == 1
    assert response_list["data"][0]["id"] == project_id_1
    # Verify slug in list
    assert response_list["data"][0]["slug"] == project_slug_1

    # Test project show using ID
    result_show_id = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'show', project_id_1])
    assert result_show_id.exit_code == 0
    response_show_id = json.loads(result_show_id.output)
    assert response_show_id["status"] == "success"
    assert response_show_id["data"]["name"] == "CLI Project 1"
    # Verify slug in show
    assert response_show_id["data"]["slug"] == project_slug_1

    # Test project show using SLUG
    result_show_slug = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'show', project_slug_1])
    assert result_show_slug.exit_code == 0
    response_show_slug = json.loads(result_show_slug.output)
    assert response_show_slug["status"] == "success"
    # Verify correct project retrieved
    assert response_show_slug["data"]["id"] == project_id_1
    assert response_show_slug["data"]["slug"] == project_slug_1

    # Test project update using SLUG
    result_update = runner.invoke(cli, ['--db-path', db_path, 'project', 'update',
                                  project_slug_1, '--name', 'Updated Project 1', '--description', 'New Desc'])
    assert result_update.exit_code == 0
    response_update = json.loads(result_update.output)
    assert response_update["status"] == "success"
    assert response_update["data"]["name"] == "Updated Project 1"
    assert response_update["data"]["description"] == "New Desc"
    # Slug should be immutable
    assert response_update["data"]["slug"] == project_slug_1


def test_cli_project_status(cli_runner_env):
    """Test creating and updating project status using slugs."""
    runner, db_path = cli_runner_env

    # Create Project with COMPLETED status
    result_create = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Status Test Proj', '--status', 'COMPLETED'])
    assert result_create.exit_code == 0
    response_create = json.loads(result_create.output)
    assert response_create['status'] == 'success'
    assert response_create['data']['status'] == 'COMPLETED'
    project_id = response_create['data']['id']
    project_slug = response_create['data']['slug']  # Get slug

    # Update status using slug
    result_update = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'update', project_slug, '--status', 'ARCHIVED'])
    assert result_update.exit_code == 0
    # Check stderr for the reminder
    assert "Reminder: Project status updated." in result_update.stderr
    response_update = json.loads(result_update.output)
    assert response_update['status'] == 'success'
    assert response_update['data']['status'] == 'ARCHIVED'

    # Show (Text) using slug and verify status
    result_show_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'show', project_slug])
    assert result_show_text.exit_code == 0
    assert "Status:      ARCHIVED" in result_show_text.output

    # List (Text) and verify status
    result_list_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list'])
    assert result_list_text.exit_code == 0
    assert "ARCHIVED" in result_list_text.output  # Check status in list output

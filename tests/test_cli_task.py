"""Tests for task CLI commands."""

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


def test_cli_task_crud(cli_runner_env):
    """Test basic task create, list, show, update via CLI using slugs."""
    runner, db_path = cli_runner_env

    # Setup: Create a project first
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Task Test Project'])
    project_data = json.loads(result_proj.output)['data']
    project_id = project_data['id']
    project_slug = project_data['slug']  # Get project slug
    assert project_slug == "task-test-project"

    # Test task creation using project slug
    result_create = runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                                  '--project', project_slug, '--name', 'CLI Task 1', '--description', 'Task Desc 1'])  # Use project slug
    assert result_create.exit_code == 0, f"Output: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    assert response_create["data"]["name"] == "CLI Task 1"
    task_id_1 = response_create["data"]["id"]
    task_slug_1 = response_create["data"]["slug"]  # Get task slug
    assert task_slug_1 == "cli-task-1"  # Verify expected task slug

    # Test task listing using project slug
    result_list = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'list', '--project', project_slug])  # Use project slug
    assert result_list.exit_code == 0
    response_list = json.loads(result_list.output)
    assert response_list["status"] == "success"
    assert len(response_list["data"]) == 1
    assert response_list["data"][0]["id"] == task_id_1
    # Verify task slug in list
    assert response_list["data"][0]["slug"] == task_slug_1

    # Test task show using project slug and task slug
    result_show = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'show', project_slug, task_slug_1])
    assert result_show.exit_code == 0
    response_show = json.loads(result_show.output)
    assert response_show["status"] == "success"
    assert response_show["data"]["name"] == "CLI Task 1"
    assert response_show["data"]["slug"] == task_slug_1  # Verify slug in show

    # Test task update using project slug and task slug
    result_update = runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                                  project_slug, task_slug_1, '--name', 'Updated Task 1', '--status', 'IN_PROGRESS'])
    assert result_update.exit_code == 0
    response_update = json.loads(result_update.output)
    assert response_update["status"] == "success"
    assert response_update["data"]["name"] == "Updated Task 1"
    assert response_update["data"]["status"] == "IN_PROGRESS"
    # Slug should be immutable
    assert response_update["data"]["slug"] == task_slug_1

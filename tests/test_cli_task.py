"""Tests for task CLI commands."""

import pytest
import json
import os
from pathlib import Path
from pm.storage import init_db, get_task
from pm.cli.__main__ import cli  # Import the main cli entry point
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
                                  # Use project slug
                                        '--project', project_slug, '--name', 'CLI Task 1', '--description', 'Task Desc 1'])
    assert result_create.exit_code == 0, f"Output: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    assert response_create["data"]["name"] == "CLI Task 1"
    task_id_1 = response_create["data"]["id"]
    task_slug_1 = response_create["data"]["slug"]  # Get task slug
    assert task_slug_1 == "cli-task-1"  # Verify expected task slug

    # Test task listing using project slug
    result_list = runner.invoke(
        # Use project slug
        cli, ['--db-path', db_path, 'task', 'list', '--project', project_slug])
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


# --- Tests for @filepath description ---

def test_task_create_description_from_file(cli_runner_env, tmp_path):
    """Test 'task create --description @filepath'."""
    runner, db_path = cli_runner_env
    # Setup: Create a project first
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'File Desc Project'])
    project_data = json.loads(result_proj.output)['data']
    project_slug = project_data['slug']

    desc_content = "Description from file.\nContains newlines.\nAnd symbols: <>?:"
    filepath = tmp_path / "task_desc.txt"
    filepath.write_text(desc_content, encoding='utf-8')

    result_create = runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                                  '--project', project_slug,
                                        '--name', 'Task With File Desc',
                                        '--description', f"@{filepath}"])

    assert result_create.exit_code == 0, f"CLI Error: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    assert response_create["data"]["description"] == desc_content
    task_id = response_create["data"]["id"]

    # Verify in DB
    conn = init_db(db_path)
    task = get_task(conn, task_id)
    conn.close()
    assert task is not None
    assert task.description == desc_content


def test_task_update_description_from_file(cli_runner_env, tmp_path):
    """Test 'task update --description @filepath'."""
    runner, db_path = cli_runner_env
    # Setup: Create a project and task
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Update File Desc Project'])
    project_data = json.loads(result_proj.output)['data']
    project_slug = project_data['slug']
    result_task = runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                                      '--project', project_slug, '--name', 'Task To Update Desc'])
    task_data = json.loads(result_task.output)['data']
    task_slug = task_data['slug']
    task_id = task_data['id']

    desc_content = "UPDATED Description from file.\nWith newlines."
    filepath = tmp_path / "updated_task_desc.txt"
    filepath.write_text(desc_content, encoding='utf-8')

    result_update = runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                                  project_slug, task_slug,
                                  '--description', f"@{filepath}"])

    assert result_update.exit_code == 0, f"CLI Error: {result_update.output}"
    response_update = json.loads(result_update.output)
    assert response_update["status"] == "success"
    assert response_update["data"]["description"] == desc_content

    # Verify in DB
    conn = init_db(db_path)
    task = get_task(conn, task_id)
    conn.close()
    assert task is not None
    assert task.description == desc_content


def test_task_create_description_from_file_not_found(cli_runner_env):
    """Test 'task create --description @filepath' with non-existent file."""
    runner, db_path = cli_runner_env
    # Setup: Create a project first
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'File Not Found Project'])
    project_data = json.loads(result_proj.output)['data']
    project_slug = project_data['slug']

    filepath = "no_such_desc_file.txt"

    result_create = runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                                  '--project', project_slug,
                                        '--name', 'Task File Not Found',
                                        '--description', f"@{filepath}"])

    assert result_create.exit_code != 0  # Should fail
    assert "Error: File not found" in result_create.stderr  # Check stderr for UsageError
    assert filepath in result_create.stderr  # Check stderr for filename too


def test_task_update_description_from_file_not_found(cli_runner_env):
    """Test 'task update --description @filepath' with non-existent file."""
    runner, db_path = cli_runner_env
    # Setup: Create a project and task
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Update File Not Found Project'])
    project_data = json.loads(result_proj.output)['data']
    project_slug = project_data['slug']
    result_task = runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                                      '--project', project_slug, '--name', 'Update Task File Not Found'])
    task_data = json.loads(result_task.output)['data']
    task_slug = task_data['slug']

    filepath = "no_such_updated_desc.txt"

    result_update = runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                                  project_slug, task_slug,
                                  '--description', f"@{filepath}"])

    assert result_update.exit_code != 0  # Should fail
    assert "Error: File not found" in result_update.stderr  # Check stderr for UsageError
    assert filepath in result_update.stderr  # Check stderr for filename too

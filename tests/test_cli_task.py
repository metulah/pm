"""Tests for task CLI commands."""

import pytest
import json
import sqlite3  # Import sqlite3
import os
from pathlib import Path
from pm.storage import init_db, get_task  # Removed get_db_connection from here
# Import get_db_connection from correct location
from pm.cli.base import get_db_connection
from pm.core.types import TaskStatus  # Import TaskStatus
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
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Task Test Project'])
    project_data = json.loads(result_proj.output)['data']
    project_id = project_data['id']
    project_slug = project_data['slug']  # Get project slug
    assert project_slug == "task-test-project"

    # Test task creation using project slug
    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
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
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--project', project_slug])
    assert result_list.exit_code == 0
    response_list = json.loads(result_list.output)
    assert response_list["status"] == "success"
    assert len(response_list["data"]) == 1
    assert response_list["data"][0]["id"] == task_id_1
    # Verify task slug in list
    assert response_list["data"][0]["slug"] == task_slug_1

    # Test task show using project slug and task slug
    result_show = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', project_slug, task_slug_1])
    assert result_show.exit_code == 0
    response_show = json.loads(result_show.output)
    assert response_show["status"] == "success"
    assert response_show["data"]["name"] == "CLI Task 1"
    assert response_show["data"]["slug"] == task_slug_1  # Verify slug in show

    # Test task update using project slug and task slug
    result_update = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'update',
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
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'File Desc Project'])
    project_data = json.loads(result_proj.output)['data']
    project_slug = project_data['slug']

    desc_content = "Description from file.\nContains newlines.\nAnd symbols: <>?:"
    filepath = tmp_path / "task_desc.txt"
    filepath.write_text(desc_content, encoding='utf-8')

    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
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
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Update File Desc Project'])
    project_data = json.loads(result_proj.output)['data']
    project_slug = project_data['slug']
    result_task = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                      '--project', project_slug, '--name', 'Task To Update Desc'])
    task_data = json.loads(result_task.output)['data']
    task_slug = task_data['slug']
    task_id = task_data['id']

    desc_content = "UPDATED Description from file.\nWith newlines."
    filepath = tmp_path / "updated_task_desc.txt"
    filepath.write_text(desc_content, encoding='utf-8')

    result_update = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'update',
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
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'File Not Found Project'])
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
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Update File Not Found Project'])
    project_data = json.loads(result_proj.output)['data']
    project_slug = project_data['slug']
    result_task = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
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


# --- Deletion Tests ---

def test_task_delete_requires_force(cli_runner_env):
    """Test that 'task delete' fails without --force."""
    runner, db_path = cli_runner_env
    # Setup: Create project and task
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Task Force Delete Project'])
    project_slug = json.loads(result_proj.output)['data']['slug']
    result_task = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                      '--project', project_slug, '--name', 'Task Force Delete Test'])
    task_slug = json.loads(result_task.output)['data']['slug']
    task_id = json.loads(result_task.output)[
        'data']['id']  # Need ID for verification

    # Attempt delete without --force
    result_delete = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'delete', project_slug, task_slug])

    # Expect failure and specific error message
    assert result_delete.exit_code != 0
    assert "Error: Deleting a task is irreversible" in result_delete.stderr
    assert "--force" in result_delete.stderr

    # Verify task still exists
    conn = init_db(db_path)
    task = get_task(conn, task_id)
    conn.close()
    assert task is not None


def test_task_delete_with_force(cli_runner_env):
    """Test that 'task delete' succeeds with --force."""
    runner, db_path = cli_runner_env
    # Setup: Create project and task
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Task Force Delete Success Project'])
    project_slug = json.loads(result_proj.output)['data']['slug']
    result_task = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                      '--project', project_slug, '--name', 'Task Force Delete Success Test'])
    task_slug = json.loads(result_task.output)['data']['slug']
    task_id = json.loads(result_task.output)[
        'data']['id']  # Need ID for verification

    # Attempt delete with --force
    result_delete = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'delete', project_slug, task_slug, '--force'])

    # Expect success
    assert result_delete.exit_code == 0
    response = json.loads(result_delete.output)
    assert response['status'] == 'success'
    assert f"Task '{task_slug}' deleted" in response['message']

    # Verify task is gone
    conn = init_db(db_path)
    task = get_task(conn, task_id)
    conn.close()
    assert task is None
# --- Abandoned Status Tests ---


@pytest.fixture
def setup_tasks_for_cli_abandon_list_test(cli_runner_env):
    """Fixture to set up project and tasks for abandon/list CLI tests."""
    runner, db_path = cli_runner_env
    # Create project
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Abandon List Test Project'])
    project_slug = json.loads(result_proj.output)['data']['slug']

    # Task 1: To be abandoned
    result_task1 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                       '--project', project_slug, '--name', 'Task To Abandon'])
    task1_slug = json.loads(result_task1.output)['data']['slug']
    task1_id = json.loads(result_task1.output)['data']['id']

    # Task 2: To be completed
    result_task2 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                       '--project', project_slug, '--name', 'Task To Complete'])
    task2_slug = json.loads(result_task2.output)['data']['slug']

    # Task 3: To remain active (IN_PROGRESS)
    result_task3 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                       '--project', project_slug, '--name', 'Active Task'])
    task3_slug = json.loads(result_task3.output)['data']['slug']
    runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                  project_slug, task3_slug, '--status', 'IN_PROGRESS'])

    # Set Task 1 to ABANDONED (via IN_PROGRESS)
    runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                  project_slug, task1_slug, '--status', 'IN_PROGRESS'])
    runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                  project_slug, task1_slug, '--status', 'ABANDONED'])

    # Set Task 2 to COMPLETED (via IN_PROGRESS)
    runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                  project_slug, task2_slug, '--status', 'IN_PROGRESS'])
    runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                  project_slug, task2_slug, '--status', 'COMPLETED'])

    return runner, db_path, project_slug, task1_slug, task1_id, task2_slug, task3_slug


def test_cli_task_update_to_abandoned(cli_runner_env):
    """Test updating a task status to ABANDONED via CLI."""
    runner, db_path = cli_runner_env
    # Setup: Create project and task
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Abandon Update Test'])
    project_slug = json.loads(result_proj.output)['data']['slug']
    result_task = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                      '--project', project_slug, '--name', 'Task To Update Abandon'])
    task_slug = json.loads(result_task.output)['data']['slug']
    task_id = json.loads(result_task.output)['data']['id']

    # Update to IN_PROGRESS first
    runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                  project_slug, task_slug, '--status', 'IN_PROGRESS'])

    # Update to ABANDONED
    result_abandon = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'update',
                                         project_slug, task_slug, '--status', 'ABANDONED'])
    assert result_abandon.exit_code == 0, f"Output: {result_abandon.output}"
    response_abandon = json.loads(result_abandon.output)
    assert response_abandon["status"] == "success"
    assert response_abandon["data"]["status"] == TaskStatus.ABANDONED.value

    # Verify in DB
    # Connect directly to the test DB path
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row  # Ensure row factory is set for attribute access
    task_db = get_task(conn, task_id)
    conn.close()
    assert task_db.status == TaskStatus.ABANDONED


def test_cli_task_list_default_hides_abandoned(setup_tasks_for_cli_abandon_list_test):
    """Test 'task list' default hides ABANDONED and COMPLETED tasks."""
    runner, db_path, project_slug, _, _, _, task3_slug = setup_tasks_for_cli_abandon_list_test

    result_list_default = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--project', project_slug])
    assert result_list_default.exit_code == 0
    response_list_default = json.loads(result_list_default.output)['data']
    assert len(response_list_default) == 1  # Only Active Task 3 should show
    assert response_list_default[0]['slug'] == task3_slug


def test_cli_task_list_with_abandoned_flag(setup_tasks_for_cli_abandon_list_test):
    """Test 'task list --abandoned' shows ABANDONED and ACTIVE tasks."""
    runner, db_path, project_slug, task1_slug, _, _, task3_slug = setup_tasks_for_cli_abandon_list_test

    result_list_abandoned = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--project', project_slug, '--abandoned'])
    assert result_list_abandoned.exit_code == 0
    response_list_abandoned = json.loads(result_list_abandoned.output)['data']
    # Abandoned Task 1 and Active Task 3
    assert len(response_list_abandoned) == 2
    slugs_abandoned = {t['slug'] for t in response_list_abandoned}
    assert task1_slug in slugs_abandoned
    assert task3_slug in slugs_abandoned


def test_cli_task_list_with_completed_flag(setup_tasks_for_cli_abandon_list_test):
    """Test 'task list --completed' shows COMPLETED and ACTIVE tasks."""
    runner, db_path, project_slug, _, _, task2_slug, task3_slug = setup_tasks_for_cli_abandon_list_test

    result_list_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--project', project_slug, '--completed'])
    assert result_list_completed.exit_code == 0
    response_list_completed = json.loads(result_list_completed.output)['data']
    # Completed Task 2 and Active Task 3
    assert len(response_list_completed) == 2
    slugs_completed = {t['slug'] for t in response_list_completed}
    assert task2_slug in slugs_completed
    assert task3_slug in slugs_completed


def test_cli_task_list_with_abandoned_and_completed_flags(setup_tasks_for_cli_abandon_list_test):
    """Test 'task list --abandoned --completed' shows all tasks."""
    runner, db_path, project_slug, task1_slug, _, task2_slug, task3_slug = setup_tasks_for_cli_abandon_list_test

    result_list_all = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--project', project_slug, '--abandoned', '--completed'])
    assert result_list_all.exit_code == 0
    response_list_all = json.loads(result_list_all.output)['data']
    assert len(response_list_all) == 3  # All tasks
    slugs_all = {t['slug'] for t in response_list_all}
    assert task1_slug in slugs_all  # Abandoned
    assert task2_slug in slugs_all  # Completed
    assert task3_slug in slugs_all  # Active

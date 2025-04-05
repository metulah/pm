"""Tests for task CLI commands related to status handling."""

import pytest
import json
import sqlite3
import os
from pathlib import Path
from pm.storage import init_db, get_task
from pm.cli.base import get_db_connection  # Keep for consistency
from pm.core.types import TaskStatus
from pm.cli.__main__ import cli
from click.testing import CliRunner

# --- Fixture for CLI Runner and DB Path ---


@pytest.fixture
def cli_runner_env(tmp_path):
    """Fixture providing a CliRunner and a temporary db_path."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)
    conn.close()
    runner = CliRunner(mix_stderr=False)
    return runner, db_path

# --- Abandoned/Completed Status Tests ---


@pytest.fixture
def setup_tasks_for_cli_status_list_test(cli_runner_env):
    """Fixture to set up project and tasks for status/list CLI tests."""
    runner, db_path = cli_runner_env
    # Create project
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Status List Test Project'])
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


def test_cli_task_list_default_hides_abandoned(setup_tasks_for_cli_status_list_test):
    """Test 'task list' default hides ABANDONED and COMPLETED tasks."""
    runner, db_path, project_slug, _, _, _, task3_slug = setup_tasks_for_cli_status_list_test

    result_list_default = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--project', project_slug])
    assert result_list_default.exit_code == 0
    response_list_default = json.loads(result_list_default.output)['data']
    assert len(response_list_default) == 1  # Only Active Task 3 should show
    assert response_list_default[0]['slug'] == task3_slug


def test_cli_task_list_with_abandoned_flag(setup_tasks_for_cli_status_list_test):
    """Test 'task list --abandoned' shows ABANDONED and ACTIVE tasks."""
    runner, db_path, project_slug, task1_slug, _, _, task3_slug = setup_tasks_for_cli_status_list_test

    result_list_abandoned = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--project', project_slug, '--abandoned'])
    assert result_list_abandoned.exit_code == 0
    response_list_abandoned = json.loads(result_list_abandoned.output)['data']
    # Abandoned Task 1 and Active Task 3
    assert len(response_list_abandoned) == 2
    slugs_abandoned = {t['slug'] for t in response_list_abandoned}
    assert task1_slug in slugs_abandoned
    assert task3_slug in slugs_abandoned


def test_cli_task_list_with_completed_flag(setup_tasks_for_cli_status_list_test):
    """Test 'task list --completed' shows COMPLETED and ACTIVE tasks."""
    runner, db_path, project_slug, _, _, task2_slug, task3_slug = setup_tasks_for_cli_status_list_test

    result_list_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--project', project_slug, '--completed'])
    assert result_list_completed.exit_code == 0
    response_list_completed = json.loads(result_list_completed.output)['data']
    # Completed Task 2 and Active Task 3
    assert len(response_list_completed) == 2
    slugs_completed = {t['slug'] for t in response_list_completed}
    assert task2_slug in slugs_completed
    assert task3_slug in slugs_completed


def test_cli_task_list_with_abandoned_and_completed_flags(setup_tasks_for_cli_status_list_test):
    """Test 'task list --abandoned --completed' shows all tasks."""
    runner, db_path, project_slug, task1_slug, _, task2_slug, task3_slug = setup_tasks_for_cli_status_list_test

    result_list_all = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'list', '--project', project_slug, '--abandoned', '--completed'])
    assert result_list_all.exit_code == 0
    response_list_all = json.loads(result_list_all.output)['data']
    assert len(response_list_all) == 3  # All tasks
    slugs_all = {t['slug'] for t in response_list_all}
    assert task1_slug in slugs_all  # Abandoned
    assert task2_slug in slugs_all  # Completed
    assert task3_slug in slugs_all  # Active

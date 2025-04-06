"""Tests for task CLI deletion commands."""

import pytest
import json
import sqlite3
import os
from pathlib import Path
from pm.storage import init_db, get_task
from pm.cli.common_utils import get_db_connection  # Import from common_utils
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

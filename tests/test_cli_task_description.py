"""Tests for task CLI commands related to description handling."""

import pytest
import json
import sqlite3
import os
from pathlib import Path
from pm.storage import init_db, get_task
# Although unused directly in these tests, keep for consistency? Or remove? Let's keep for now.
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

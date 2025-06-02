"""Tests for CLI command workflows related to moving tasks."""

import pytest
import json
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

# --- Move Workflow Tests ---


def test_cli_task_move(cli_runner_env):
    """Test moving a task between projects using slugs."""
    runner, db_path = cli_runner_env

    # Setup: Create Project A and Project B
    result_a = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Project A'])
    project_a_data = json.loads(result_a.output)['data']
    project_a_id = project_a_data['id']
    project_a_slug = project_a_data['slug']
    result_b = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Project B'])
    project_b_data = json.loads(result_b.output)['data']
    project_b_id = project_b_data['id']
    project_b_slug = project_b_data['slug']

    # Create Task 1 in Project A
    result_task = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'create', '--project', project_a_slug, '--name', 'Task 1'])  # Use slug
    task_1_data = json.loads(result_task.output)['data']
    task_1_slug = task_1_data['slug']

    # Verify Task 1 is in Project A (using slugs)
    result_show = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', project_a_slug, task_1_slug])
    assert json.loads(result_show.output)['data']['project_id'] == project_a_id

    # Attempt to move Task 1 (using slugs) to non-existent project (should fail)
    result_move_fail = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'update', project_a_slug, task_1_slug, '--project', 'non-existent-project'])
    assert result_move_fail.exit_code == 0  # CLI handles error
    response_fail = json.loads(result_move_fail.output)
    assert response_fail['status'] == 'error'
    # Note: Error message comes from resolver now
    assert "Project not found with identifier: 'non-existent-project'" in response_fail['message']

    # Move Task 1 (using slugs) to Project B (using slug) (should succeed)
    result_move_ok = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'update', project_a_slug, task_1_slug, '--project', project_b_slug])
    assert result_move_ok.exit_code == 0
    response_ok = json.loads(result_move_ok.output)
    assert response_ok['status'] == 'success'
    assert response_ok['data']['project_id'] == project_b_id

    # Verify Task 1 is now in Project B (using project B slug and task slug)
    result_show_after = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', project_b_slug, task_1_slug])
    assert json.loads(result_show_after.output)[
        'data']['project_id'] == project_b_id

"""Tests for CLI command integrations and interactions."""

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

# --- CLI Integration Tests ---


def test_cli_project_delete_standard(cli_runner_env):
    """Test standard project deletion logic (fail with task, success empty) using slugs."""
    runner, db_path = cli_runner_env

    # Setup: Create project and task
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Delete Test Project'])
    project_data = json.loads(result_proj.output)['data']
    project_id = project_data['id']
    project_slug = project_data['slug']
    result_task = runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                                      '--project', project_slug, '--name', 'Task In Delete Project'])  # Use slug
    task_data = json.loads(result_task.output)['data']
    task_id = task_data['id']
    task_slug = task_data['slug']

    # Test deleting project (using slug) with task (should fail)
    result_del_fail = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_slug])
    assert result_del_fail.exit_code == 0  # CLI handles error gracefully
    response_del_fail = json.loads(result_del_fail.output)
    assert response_del_fail["status"] == "error"
    assert "Cannot delete project" in response_del_fail["message"]
    assert "contains 1 task(s)" in response_del_fail["message"]

    # Test deleting the task (using project slug and task slug)
    result_del_task = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'delete', project_slug, task_slug])
    assert result_del_task.exit_code == 0
    assert json.loads(result_del_task.output)["status"] == "success"

    # Test deleting project (using slug) without task (should succeed)
    result_del_ok = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_slug])
    assert result_del_ok.exit_code == 0
    response_del_ok = json.loads(result_del_ok.output)
    assert response_del_ok["status"] == "success"
    assert "deleted" in response_del_ok["message"]

    # Verify project is gone (using slug)
    result_show = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'show', project_slug])
    assert result_show.exit_code == 0
    assert json.loads(result_show.output)["status"] == "error"
    assert "not found" in json.loads(result_show.output)["message"]


def test_cli_task_move(cli_runner_env):
    """Test moving a task between projects using slugs."""
    runner, db_path = cli_runner_env

    # Setup: Create Project A and Project B
    result_a = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Project A'])
    project_a_data = json.loads(result_a.output)['data']
    project_a_id = project_a_data['id']
    project_a_slug = project_a_data['slug']
    result_b = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Project B'])
    project_b_data = json.loads(result_b.output)['data']
    project_b_id = project_b_data['id']
    project_b_slug = project_b_data['slug']

    # Create Task 1 in Project A
    result_task = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_a_slug, '--name', 'Task 1'])  # Use slug
    task_1_data = json.loads(result_task.output)['data']
    task_1_id = task_1_data['id']
    task_1_slug = task_1_data['slug']

    # Verify Task 1 is in Project A (using slugs)
    result_show = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'show', project_a_slug, task_1_slug])
    assert json.loads(result_show.output)['data']['project_id'] == project_a_id

    # Attempt to move Task 1 (using slugs) to non-existent project (should fail)
    result_move_fail = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'update', project_a_slug, task_1_slug, '--project', 'non-existent-project'])
    assert result_move_fail.exit_code == 0  # CLI handles error
    response_fail = json.loads(result_move_fail.output)
    assert response_fail['status'] == 'error'
    # Note: Error message comes from resolver now
    assert "Project not found with identifier: 'non-existent-project'" in response_fail['message']

    # Move Task 1 (using slugs) to Project B (using slug) (should succeed)
    result_move_ok = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'update', project_a_slug, task_1_slug, '--project', project_b_slug])
    assert result_move_ok.exit_code == 0
    response_ok = json.loads(result_move_ok.output)
    assert response_ok['status'] == 'success'
    assert response_ok['data']['project_id'] == project_b_id

    # Verify Task 1 is now in Project B (using project B slug and task slug)
    result_show_after = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'show', project_b_slug, task_1_slug])
    assert json.loads(result_show_after.output)[
        'data']['project_id'] == project_b_id


def test_cli_project_delete_force(cli_runner_env):
    """Test force deleting a project with tasks using slugs."""
    runner, db_path = cli_runner_env

    # Setup: Create Project C with Task 2 and Task 3
    result_c = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Project C'])
    project_c_data = json.loads(result_c.output)['data']
    project_c_id = project_c_data['id']
    project_c_slug = project_c_data['slug']
    result_task2 = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_c_slug, '--name', 'Task 2'])  # Use slug
    task_2_data = json.loads(result_task2.output)['data']
    task_2_id = task_2_data['id']
    task_2_slug = task_2_data['slug']
    result_task3 = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_c_slug, '--name', 'Task 3'])  # Use slug
    task_3_data = json.loads(result_task3.output)['data']
    task_3_id = task_3_data['id']
    task_3_slug = task_3_data['slug']

    # Attempt delete without force (using slug) (should fail)
    result_del_noforce = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_c_slug])
    assert result_del_noforce.exit_code == 0  # CLI handles error
    response_del_noforce = json.loads(result_del_noforce.output)
    assert response_del_noforce['status'] == 'error'
    assert "Cannot delete project" in response_del_noforce['message']
    assert "contains 2 task(s)" in response_del_noforce['message']

    # Attempt delete with force (using slug) (should succeed)
    result_del_force = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_c_slug, '--force'])
    assert result_del_force.exit_code == 0
    response_del_force = json.loads(result_del_force.output)
    assert response_del_force['status'] == 'success'
    assert "deleted" in response_del_force['message']

    # Verify Project C is gone (using slug)
    result_show_c = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'show', project_c_slug])
    assert json.loads(result_show_c.output)['status'] == 'error'
    assert "not found" in json.loads(result_show_c.output)['message']

    # Verify Task 2 is gone (using project slug and task slug)
    # Need to use the original project slug here as the project is gone
    result_show_t2 = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'show', project_c_slug, task_2_slug])
    assert json.loads(result_show_t2.output)['status'] == 'error'
    # The error should come from the project resolver first
    assert "Project not found with identifier" in json.loads(result_show_t2.output)[
        'message']

    # Verify Task 3 is gone (using project slug and task slug)
    result_show_t3 = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'show', project_c_slug, task_3_slug])
    assert json.loads(result_show_t3.output)['status'] == 'error'
    assert "Project not found with identifier" in json.loads(result_show_t3.output)[
        'message']


def test_cli_output_format(cli_runner_env):
    """Test --format text vs json for list and show using slugs."""
    runner, db_path = cli_runner_env

    # Setup: Create a project and a task
    result_proj = runner.invoke(cli, ['--db-path', db_path, 'project', 'create',
                                '--name', 'Format Test Proj', '--description', 'Format Desc'])
    project_data = json.loads(result_proj.output)['data']
    project_id = project_data['id']
    project_slug = project_data['slug']
    result_task = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_slug, '--name', 'Format Test Task'])  # Use slug
    task_data = json.loads(result_task.output)['data']
    task_id = task_data['id']
    task_slug = task_data['slug']

    # Test project list (Text format)
    result_list_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list'])
    assert result_list_text.exit_code == 0
    # Check that ID is NOT present by default in text format
    assert "ID" not in result_list_text.output
    assert project_slug in result_list_text.output  # Check slug is present

    # Test project list with --id flag (Text format)
    result_list_text_id = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--id'])
    assert result_list_text_id.exit_code == 0
    # Check that ID IS present when --id flag is used
    assert "ID" in result_list_text_id.output
    assert project_slug in result_list_text_id.output
    assert "NAME" in result_list_text.output
    assert "SLUG" in result_list_text.output  # Check slug column
    assert "STATUS" in result_list_text.output
    assert "Format Test Proj" in result_list_text.output
    assert project_slug in result_list_text.output  # Check slug value
    # assert project_id in result_list_text.output # Removed: ID value is not shown by default

    # Test project show (Text format) using slug
    result_show_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'show', project_slug])
    assert result_show_text.exit_code == 0
    assert f"Id:          {project_id}" in result_show_text.output
    assert "Name:        Format Test Proj" in result_show_text.output
    # Check slug field
    assert f"Slug:        {project_slug}" in result_show_text.output
    assert "Description: Format Desc" in result_show_text.output
    assert "Status:      ACTIVE" in result_show_text.output

    # Test task list (Text format) using project slug
    result_task_list_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', project_slug])  # Use slug
    assert result_task_list_text.exit_code == 0
    # Check that ID is NOT present by default in text format
    assert "ID" not in result_task_list_text.output
    assert "NAME" in result_task_list_text.output
    assert "SLUG" in result_task_list_text.output  # Check task slug column
    assert "PROJECT_SLUG" in result_task_list_text.output  # Check project slug column
    assert "STATUS" in result_task_list_text.output
    assert "Format Test Task" in result_task_list_text.output
    # assert task_id in result_task_list_text.output # Removed: ID value not shown by default
    assert task_slug in result_task_list_text.output  # Check task slug value
    assert project_slug in result_task_list_text.output  # Check project slug value

    # Test task list with --id flag (Text format)
    result_task_list_text_id = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', project_slug, '--id'])
    assert result_task_list_text_id.exit_code == 0
    # Check that ID IS present when --id flag is used
    assert "ID" in result_task_list_text_id.output
    assert task_slug in result_task_list_text_id.output
    assert project_slug in result_task_list_text_id.output

    # Test task show (Text format) using slugs
    result_task_show_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'show', project_slug, task_slug])
    assert result_task_show_text.exit_code == 0
    assert f"Id:          {task_id}" in result_task_show_text.output
    assert f"Project Id:  {project_id}" in result_task_show_text.output
    assert "Name:        Format Test Task" in result_task_show_text.output
    # Check slug field
    assert f"Slug:        {task_slug}" in result_task_show_text.output
    assert "Status:      NOT_STARTED" in result_task_show_text.output


def test_cli_simple_messages(cli_runner_env):
    """Test text format output for simple success/error messages using slugs."""
    runner, db_path = cli_runner_env

    # Setup: Create a project
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Message Test Proj'])
    project_data = json.loads(result_proj.output)['data']
    project_id = project_data['id']
    project_slug = project_data['slug']

    # Test delete success message (Text format) using slug
    result_del_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'delete', project_slug])
    assert result_del_text.exit_code == 0
    # Check message uses identifier
    assert f"Success: Project '{project_slug}' deleted" in result_del_text.output

    # Test delete error message (Text format) using non-existent slug
    result_del_err_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'delete', 'non-existent-slug'])
    assert result_del_err_text.exit_code == 0
    # Check resolver error message
    assert "Error: Project not found with identifier: 'non-existent-slug'" in result_del_err_text.output

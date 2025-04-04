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

    # Setup: Create an active project/task and a completed project/task
    result_proj_active = runner.invoke(cli, ['--db-path', db_path, 'project', 'create',
                                             '--name', 'Format Active Proj', '--description', 'Active Desc', '--status', 'ACTIVE'])
    proj_active_data = json.loads(result_proj_active.output)['data']
    proj_active_id = proj_active_data['id']
    proj_active_slug = proj_active_data['slug']

    result_proj_completed = runner.invoke(cli, ['--db-path', db_path, 'project', 'create',
                                                '--name', 'Format Completed Proj', '--description', 'Completed Desc', '--status', 'COMPLETED'])
    proj_completed_data = json.loads(result_proj_completed.output)['data']
    proj_completed_id = proj_completed_data['id']
    proj_completed_slug = proj_completed_data['slug']

    result_task_active = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', proj_active_slug, '--name', 'Format Active Task', '--status', 'IN_PROGRESS'])
    task_active_data = json.loads(result_task_active.output)['data']
    task_active_id = task_active_data['id']
    task_active_slug = task_active_data['slug']

    result_task_completed = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', proj_active_slug, '--name', 'Format Completed Task', '--status', 'COMPLETED'])
    task_completed_data = json.loads(result_task_completed.output)['data']
    task_completed_id = task_completed_data['id']
    task_completed_slug = task_completed_data['slug']

    # Test project list (Text format - default, should hide completed)
    result_list_text_default = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list'])
    assert result_list_text_default.exit_code == 0
    assert "ID" not in result_list_text_default.output  # ID hidden
    # Description hidden by default
    assert "DESCRIPTION" not in result_list_text_default.output
    assert "Active Desc" not in result_list_text_default.output
    assert proj_active_slug in result_list_text_default.output  # Active project shown
    # Completed project hidden
    assert proj_completed_slug not in result_list_text_default.output

    # Test project list (Text format - with --completed)
    result_list_text_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--completed'])
    assert result_list_text_completed.exit_code == 0
    assert "ID" not in result_list_text_completed.output  # ID still hidden
    # Description still hidden
    assert "DESCRIPTION" not in result_list_text_completed.output
    assert proj_active_slug in result_list_text_completed.output  # Active project shown
    # Completed project shown
    assert proj_completed_slug in result_list_text_completed.output

    # Test project list with --id and --completed flags (Text format)
    result_list_text_id_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--id', '--completed'])
    assert result_list_text_id_completed.exit_code == 0
    assert "ID" in result_list_text_id_completed.output  # ID shown
    # Description still hidden
    assert "DESCRIPTION" not in result_list_text_id_completed.output
    assert proj_active_slug in result_list_text_id_completed.output
    assert proj_completed_slug in result_list_text_id_completed.output

    # Test project list with --description flag (Text format)
    result_list_text_desc = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--description'])
    assert result_list_text_desc.exit_code == 0
    assert "ID" not in result_list_text_desc.output  # ID hidden
    assert "DESCRIPTION" in result_list_text_desc.output  # Description shown
    assert "Active Desc" in result_list_text_desc.output
    assert proj_active_slug in result_list_text_desc.output
    # Completed still hidden by default
    assert proj_completed_slug not in result_list_text_desc.output

    # Test project list with --id, --completed, and --description flags (Text format)
    result_list_text_all_flags = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--id', '--completed', '--description'])
    assert result_list_text_all_flags.exit_code == 0
    assert "ID" in result_list_text_all_flags.output  # ID shown
    assert "DESCRIPTION" in result_list_text_all_flags.output  # Description shown
    assert "Active Desc" in result_list_text_all_flags.output
    assert "Completed Desc" in result_list_text_all_flags.output
    assert proj_active_slug in result_list_text_all_flags.output
    assert proj_completed_slug in result_list_text_all_flags.output
    # Check headers and content for the --id --completed case
    assert "NAME" in result_list_text_id_completed.output
    assert "SLUG" in result_list_text_id_completed.output
    assert "STATUS" in result_list_text_id_completed.output
    assert "Format Active Proj" in result_list_text_id_completed.output
    assert "Format Completed Proj" in result_list_text_id_completed.output

    # Test project show (Text format) using active slug
    result_show_text_active = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'show', proj_active_slug])
    assert result_show_text_active.exit_code == 0
    assert f"Id:          {proj_active_id}" in result_show_text_active.output
    assert "Name:        Format Active Proj" in result_show_text_active.output
    assert f"Slug:        {proj_active_slug}" in result_show_text_active.output
    assert "Description: Active Desc" in result_show_text_active.output
    assert "Status:      ACTIVE" in result_show_text_active.output

    # Test task list (Text format - default, should hide completed task)
    result_task_list_default = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', proj_active_slug])
    assert result_task_list_default.exit_code == 0
    assert "ID" not in result_task_list_default.output  # ID hidden
    assert "DESCRIPTION" not in result_task_list_default.output  # Description hidden
    assert task_active_slug in result_task_list_default.output  # Active task shown
    # Completed task hidden
    assert task_completed_slug not in result_task_list_default.output

    # Test task list (Text format - with --completed)
    result_task_list_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', proj_active_slug, '--completed'])
    assert result_task_list_completed.exit_code == 0
    assert "ID" not in result_task_list_completed.output  # ID hidden
    assert "DESCRIPTION" not in result_task_list_completed.output  # Description hidden
    assert task_active_slug in result_task_list_completed.output  # Active task shown
    assert task_completed_slug in result_task_list_completed.output  # Completed task shown

    # Test task list with --id and --completed flags (Text format)
    result_task_list_id_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', proj_active_slug, '--id', '--completed'])
    assert result_task_list_id_completed.exit_code == 0
    assert "ID" in result_task_list_id_completed.output  # ID shown
    assert "DESCRIPTION" not in result_task_list_id_completed.output  # Description hidden
    assert task_active_slug in result_task_list_id_completed.output
    assert task_completed_slug in result_task_list_id_completed.output
    # Project slug still present
    assert proj_active_slug in result_task_list_id_completed.output

    # Test task list with --description flag (Text format)
    result_task_list_desc = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', proj_active_slug, '--description'])
    assert result_task_list_desc.exit_code == 0
    assert "ID" not in result_task_list_desc.output  # ID hidden
    assert "DESCRIPTION" in result_task_list_desc.output  # Description shown
    assert task_active_slug in result_task_list_desc.output
    assert task_completed_slug not in result_task_list_desc.output  # Completed hidden

    # Test task list with all flags (Text format)
    result_task_list_all = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', proj_active_slug, '--id', '--completed', '--description'])
    assert result_task_list_all.exit_code == 0
    assert "ID" in result_task_list_all.output  # ID shown
    assert "DESCRIPTION" in result_task_list_all.output  # Description shown
    assert task_active_slug in result_task_list_all.output
    assert task_completed_slug in result_task_list_all.output
    assert proj_active_slug in result_task_list_all.output

    # Test task show (Text format) using active slugs
    result_task_show_active = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'show', proj_active_slug, task_active_slug])
    assert result_task_show_active.exit_code == 0
    assert f"Id:          {task_active_id}" in result_task_show_active.output
    # Show still shows ID
    assert f"Project Id:  {proj_active_id}" in result_task_show_active.output
    assert "Name:        Format Active Task" in result_task_show_active.output
    assert f"Slug:        {task_active_slug}" in result_task_show_active.output
    assert "Status:      IN_PROGRESS" in result_task_show_active.output


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

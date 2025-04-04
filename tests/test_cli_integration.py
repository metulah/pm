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
        # Use slug
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_a_slug, '--name', 'Task 1'])
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
        # Use slug
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_c_slug, '--name', 'Task 2'])
    task_2_data = json.loads(result_task2.output)['data']
    task_2_id = task_2_data['id']
    task_2_slug = task_2_data['slug']
    result_task3 = runner.invoke(
        # Use slug
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_c_slug, '--name', 'Task 3'])
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

    # Create CANCELLED project
    result_proj_cancelled = runner.invoke(cli, ['--db-path', db_path, 'project', 'create',
                                                '--name', 'Format Cancelled Proj', '--description', 'Cancelled Desc', '--status', 'CANCELLED'])
    proj_cancelled_data = json.loads(result_proj_cancelled.output)['data']
    proj_cancelled_id = proj_cancelled_data['id']
    proj_cancelled_slug = proj_cancelled_data['slug']

    # Update COMPLETED project to ARCHIVED
    # Note: The update command itself will be tested separately for transition logic
    runner.invoke(cli, ['--db-path', db_path, 'project',
                  'update', proj_completed_slug, '--status', 'ARCHIVED'])
    proj_archived_slug = proj_completed_slug  # Slug remains the same
    proj_archived_id = proj_completed_id

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

    # Remove assertions referencing the deleted variable result_list_text_all_flags

    # Test project list with --archived flag (Text format)
    result_list_text_arch = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--archived'])
    assert result_list_text_arch.exit_code == 0
    assert "ID" not in result_list_text_arch.output  # ID hidden
    assert "DESCRIPTION" not in result_list_text_arch.output  # Desc hidden
    assert proj_active_slug in result_list_text_arch.output  # Active shown
    assert proj_completed_slug in result_list_text_arch.output  # Archived shown
    assert proj_cancelled_slug in result_list_text_arch.output  # Cancelled shown

    # Test project list with --completed and --archived flags (shows all non-hidden cols)
    result_list_text_comp_arch = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--completed', '--archived'])
    assert result_list_text_comp_arch.exit_code == 0
    assert "ID" not in result_list_text_comp_arch.output
    assert "DESCRIPTION" not in result_list_text_comp_arch.output
    assert proj_active_slug in result_list_text_comp_arch.output
    assert proj_completed_slug in result_list_text_comp_arch.output  # Archived
    assert proj_cancelled_slug in result_list_text_comp_arch.output  # Cancelled

    # Test project list with all flags (shows all projects, all cols)
    result_list_text_all_flags_inc_arch = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--id', '--completed', '--archived', '--description'])
    assert result_list_text_all_flags_inc_arch.exit_code == 0
    assert "ID" in result_list_text_all_flags_inc_arch.output
    assert "DESCRIPTION" in result_list_text_all_flags_inc_arch.output
    assert proj_active_slug in result_list_text_all_flags_inc_arch.output
    assert proj_completed_slug in result_list_text_all_flags_inc_arch.output  # Archived
    assert proj_cancelled_slug in result_list_text_all_flags_inc_arch.output  # Cancelled

    # Test project list with --archived flag (Text format)
    result_list_text_arch = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--archived'])
    assert result_list_text_arch.exit_code == 0
    assert "ID" not in result_list_text_arch.output  # ID hidden
    assert "DESCRIPTION" not in result_list_text_arch.output  # Desc hidden
    assert proj_active_slug in result_list_text_arch.output  # Active shown
    assert proj_completed_slug in result_list_text_arch.output  # Archived shown
    assert proj_cancelled_slug in result_list_text_arch.output  # Cancelled shown

    # Test project list with --completed and --archived flags (shows all non-hidden cols)
    result_list_text_comp_arch = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--completed', '--archived'])
    assert result_list_text_comp_arch.exit_code == 0
    assert "ID" not in result_list_text_comp_arch.output
    assert "DESCRIPTION" not in result_list_text_comp_arch.output
    assert proj_active_slug in result_list_text_comp_arch.output
    assert proj_completed_slug in result_list_text_comp_arch.output  # Archived
    assert proj_cancelled_slug in result_list_text_comp_arch.output  # Cancelled

    # Test project list with all flags (shows all projects, all cols)
    result_list_text_all_flags_inc_arch = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--id', '--completed', '--archived', '--description'])
    assert result_list_text_all_flags_inc_arch.exit_code == 0
    assert "ID" in result_list_text_all_flags_inc_arch.output
    assert "DESCRIPTION" in result_list_text_all_flags_inc_arch.output
    assert proj_active_slug in result_list_text_all_flags_inc_arch.output
    assert proj_completed_slug in result_list_text_all_flags_inc_arch.output  # Archived
    assert proj_cancelled_slug in result_list_text_all_flags_inc_arch.output  # Cancelled
    # Remove assertions referencing the deleted variable result_list_text_id_completed
    # Check content in all flags output
    assert "Format Active Proj" in result_list_text_all_flags_inc_arch.output
    # This is the ARCHIVED one
    assert "Format Completed Proj" in result_list_text_all_flags_inc_arch.output
    assert "Format Cancelled Proj" in result_list_text_all_flags_inc_arch.output

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


def test_project_status_transitions(cli_runner_env):
    """Test valid and invalid project status transitions."""
    runner, db_path = cli_runner_env

    # 1. Create an ACTIVE project
    result_active = runner.invoke(cli, ['--db-path', db_path, 'project', 'create',
                                        '--name', 'Transition Test Proj'])
    proj_data = json.loads(result_active.output)['data']
    proj_slug = proj_data['slug']
    assert proj_data['status'] == 'ACTIVE'

    # 2. Test invalid transition: ACTIVE -> ARCHIVED (should fail)
    result_invalid_1 = runner.invoke(cli, ['--db-path', db_path, 'project', 'update',
                                           proj_slug, '--status', 'ARCHIVED'])
    assert result_invalid_1.exit_code == 0  # CLI handles error
    assert json.loads(result_invalid_1.output)['status'] == 'error'
    assert "Invalid project status transition: ACTIVE -> ARCHIVED" in json.loads(
        result_invalid_1.output)['message']

    # 3. Test valid transition: ACTIVE -> COMPLETED
    result_valid_1 = runner.invoke(cli, ['--db-path', db_path, 'project', 'update',
                                         proj_slug, '--status', 'COMPLETED'])
    assert result_valid_1.exit_code == 0
    assert json.loads(result_valid_1.output)['status'] == 'success'
    assert json.loads(result_valid_1.output)['data']['status'] == 'COMPLETED'

    # 4. Test invalid transition: COMPLETED -> ACTIVE (not currently allowed)
    result_invalid_2 = runner.invoke(cli, ['--db-path', db_path, 'project', 'update',
                                           proj_slug, '--status', 'ACTIVE'])
    assert result_invalid_2.exit_code == 0
    assert json.loads(result_invalid_2.output)['status'] == 'error'
    assert "Invalid project status transition: COMPLETED -> ACTIVE" in json.loads(
        result_invalid_2.output)['message']

    # 5. Test valid transition: COMPLETED -> ARCHIVED
    result_valid_2 = runner.invoke(cli, ['--db-path', db_path, 'project', 'update',
                                         proj_slug, '--status', 'ARCHIVED'])
    assert result_valid_2.exit_code == 0
    assert json.loads(result_valid_2.output)['status'] == 'success'
    assert json.loads(result_valid_2.output)['data']['status'] == 'ARCHIVED'

    # 6. Test invalid transition: ARCHIVED -> COMPLETED (not currently allowed)
    result_invalid_3 = runner.invoke(cli, ['--db-path', db_path, 'project', 'update',
                                           proj_slug, '--status', 'COMPLETED'])
    assert result_invalid_3.exit_code == 0
    assert json.loads(result_invalid_3.output)['status'] == 'error'
    assert "Invalid project status transition: ARCHIVED -> COMPLETED" in json.loads(
        result_invalid_3.output)['message']

    # 7. Create another ACTIVE project for CANCELLED test
    result_active_2 = runner.invoke(cli, ['--db-path', db_path, 'project', 'create',
                                          '--name', 'Cancel Test Proj'])
    proj_data_2 = json.loads(result_active_2.output)['data']
    proj_slug_2 = proj_data_2['slug']

    # 8. Test valid transition: ACTIVE -> CANCELLED
    result_valid_3 = runner.invoke(cli, ['--db-path', db_path, 'project', 'update',
                                         proj_slug_2, '--status', 'CANCELLED'])
    assert result_valid_3.exit_code == 0
    assert json.loads(result_valid_3.output)['status'] == 'success'
    assert json.loads(result_valid_3.output)['data']['status'] == 'CANCELLED'

    # 9. Test valid transition: CANCELLED -> ARCHIVED
    result_valid_4 = runner.invoke(cli, ['--db-path', db_path, 'project', 'update',
                                         proj_slug_2, '--status', 'ARCHIVED'])
    assert result_valid_4.exit_code == 0
    assert json.loads(result_valid_4.output)['status'] == 'success'
    assert json.loads(result_valid_4.output)['data']['status'] == 'ARCHIVED'

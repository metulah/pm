import json
import sqlite3
from pm.storage import init_db, get_task
from pm.core.types import TaskStatus
from pm.cli.__main__ import cli


def test_task_update_basic(task_cli_runner_env):
    """Test basic task update for name and status using slugs."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create a task first
    task_name = "Update Task 1"
    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                        '--project', project_slug, '--name', task_name])
    assert result_create.exit_code == 0
    task_slug = json.loads(result_create.output)['data']['slug']
    task_id = json.loads(result_create.output)['data']['id']
    assert task_slug == "update-task-1"

    # Test task update using project slug and task slug
    result_update = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'update',
                                  project_slug, task_slug, '--name', 'Updated Task Name 1', '--status', 'IN_PROGRESS'])
    assert result_update.exit_code == 0
    response_update = json.loads(result_update.output)
    assert response_update["status"] == "success"
    assert response_update["data"]["name"] == "Updated Task Name 1"
    assert response_update["data"]["status"] == TaskStatus.IN_PROGRESS.value
    # Slug should be immutable
    assert response_update["data"]["slug"] == task_slug
    assert response_update["data"]["id"] == task_id  # Ensure ID hasn't changed

    # Verify in DB
    conn = init_db(db_path)
    task = get_task(conn, task_id)
    conn.close()
    assert task is not None
    assert task.name == "Updated Task Name 1"
    assert task.status == TaskStatus.IN_PROGRESS
    assert task.slug == task_slug


def test_task_update_description_from_file(task_cli_runner_env, tmp_path):
    """Test 'task update --description @filepath'."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create a task first
    task_name = "Update Desc Task 1"
    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                        '--project', project_slug, '--name', task_name])
    assert result_create.exit_code == 0
    task_slug = json.loads(result_create.output)['data']['slug']
    task_id = json.loads(result_create.output)['data']['id']

    desc_content = "UPDATED Description from file for update test.\nWith newlines."
    filepath = tmp_path / "updated_task_desc_test.txt"
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


def test_task_update_description_from_file_not_found(task_cli_runner_env):
    """Test 'task update --description @filepath' with non-existent file."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create a task first
    task_name = "Update Desc Not Found Task"
    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                        '--project', project_slug, '--name', task_name])
    assert result_create.exit_code == 0
    task_slug = json.loads(result_create.output)['data']['slug']

    filepath = "no_such_updated_desc_test.txt"

    result_update = runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                                  project_slug, task_slug,
                                  '--description', f"@{filepath}"])

    assert result_update.exit_code != 0  # Should fail
    assert "Error: File not found" in result_update.stderr
    assert filepath in result_update.stderr


def test_cli_task_update_to_abandoned(task_cli_runner_env):
    """Test updating a task status to ABANDONED via CLI."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create a task first
    task_name = "Abandon Update Task"
    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                        '--project', project_slug, '--name', task_name])
    assert result_create.exit_code == 0
    task_slug = json.loads(result_create.output)['data']['slug']
    task_id = json.loads(result_create.output)['data']['id']

    # Update to IN_PROGRESS first (required for ABANDONED transition)
    result_progress = runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                                          project_slug, task_slug, '--status', 'IN_PROGRESS'])
    assert result_progress.exit_code == 0

    # Update to ABANDONED
    result_abandon = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'update',
                                         project_slug, task_slug, '--status', 'ABANDONED'])
    assert result_abandon.exit_code == 0, f"Output: {result_abandon.output}"
    response_abandon = json.loads(result_abandon.output)
    assert response_abandon["status"] == "success"
    assert response_abandon["data"]["status"] == TaskStatus.ABANDONED.value

    # Verify in DB
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    task_db = get_task(conn, task_id)
    conn.close()
    assert task_db is not None
    assert task_db.status == TaskStatus.ABANDONED


def test_task_update_not_found(task_cli_runner_env):
    """Test updating a non-existent task."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']
    non_existent_task_slug = "non-existent-update-task"

    result_update = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'update',
                                  project_slug, non_existent_task_slug, '--name', 'Wont Happen'])

    # Command should succeed but return error status
    assert result_update.exit_code == 0
    response_update = json.loads(result_update.output)
    assert response_update["status"] == "error"
    assert "Task not found" in response_update["message"]
    assert non_existent_task_slug in response_update["message"]


def test_task_update_status_case_insensitive(task_cli_runner_env):
    """Test updating task status with case-insensitive values."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # 1. Create Task (Default status NOT_STARTED)
    task_name = "Case Test Task"
    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                        '--project', project_slug, '--name', task_name])
    assert result_create.exit_code == 0, f"Create failed: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create['status'] == 'success'
    task_slug = response_create['data']['slug']
    assert response_create['data']['status'] == 'NOT_STARTED'

    # 2. Test lowercase status: not_started -> in_progress
    result_update_lower = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'update', project_slug, task_slug, '--status', 'in_progress'])
    assert result_update_lower.exit_code == 0, f"Update not_started->in_progress (lowercase) failed: {result_update_lower.output}"
    response_update_lower = json.loads(result_update_lower.output)
    assert response_update_lower['status'] == 'success'
    assert response_update_lower['data']['status'] == 'IN_PROGRESS', "Status should be stored as uppercase IN_PROGRESS"
    assert "Reminder: Task status updated." in result_update_lower.stderr

    # 3. Test mixed-case status: IN_PROGRESS -> Blocked
    result_update_mixed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'update', project_slug, task_slug, '--status', 'Blocked'])
    assert result_update_mixed.exit_code == 0, f"Update IN_PROGRESS->Blocked (mixed-case) failed: {result_update_mixed.output}"
    response_update_mixed = json.loads(result_update_mixed.output)
    assert response_update_mixed['status'] == 'success'
    assert response_update_mixed['data']['status'] == 'BLOCKED', "Status should be stored as uppercase BLOCKED"
    assert "Reminder: Task status updated." in result_update_mixed.stderr

    # 4. Test valid transition: BLOCKED -> in_progress (lowercase)
    result_update_blocked_to_progress = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'update', project_slug, task_slug, '--status', 'in_progress'])
    assert result_update_blocked_to_progress.exit_code == 0, f"Update BLOCKED->in_progress (lowercase) failed: {result_update_blocked_to_progress.output}"
    response_update_b2p = json.loads(result_update_blocked_to_progress.output)
    assert response_update_b2p['status'] == 'success'
    assert response_update_b2p['data']['status'] == 'IN_PROGRESS', "Status should be stored as uppercase IN_PROGRESS"
    assert "Reminder: Task status updated." in result_update_blocked_to_progress.stderr

    # 5. Test valid transition: IN_PROGRESS -> COMPLETED (uppercase baseline)
    result_update_progress_to_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'update', project_slug, task_slug, '--status', 'COMPLETED'])
    assert result_update_progress_to_completed.exit_code == 0, f"Update IN_PROGRESS->COMPLETED (uppercase) failed: {result_update_progress_to_completed.output}"
    response_update_p2c = json.loads(
        result_update_progress_to_completed.output)
    assert response_update_p2c['status'] == 'success'
    assert response_update_p2c['data']['status'] == 'COMPLETED', "Status should be stored as uppercase COMPLETED"
    assert "Reminder: Task status updated." in result_update_progress_to_completed.stderr

    # 6. Test invalid status value (should fail regardless of case)
    # Note: Task is now COMPLETED, so any update should fail based on transition rules
    result_update_invalid = runner.invoke(
        # Try moving back to IN_PROGRESS
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'update', project_slug, task_slug, '--status', 'in_progress'])
    assert result_update_invalid.exit_code != 0, "Update from COMPLETED status should fail"
    # Check for the specific transition error from the storage layer
    assert "Invalid status transition: COMPLETED -> IN_PROGRESS" in result_update_invalid.stderr

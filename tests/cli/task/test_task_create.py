import json
from pm.storage import init_db, get_task
from pm.core.types import TaskStatus
from pm.cli.__main__ import cli


def test_task_create_basic(task_cli_runner_env):
    """Test basic task creation using the default project slug."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                        '--project', project_slug,
                                        '--name', 'CLI Task Create 1',
                                        '--description', 'Task Desc 1'])

    assert result_create.exit_code == 0, f"Output: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    assert response_create["data"]["name"] == "CLI Task Create 1"
    assert response_create["data"]["description"] == "Task Desc 1"
    # Default status should be NOT_STARTED
    assert response_create["data"]["status"] == TaskStatus.NOT_STARTED.value
    task_id_1 = response_create["data"]["id"]
    task_slug_1 = response_create["data"]["slug"]
    assert task_slug_1 == "cli-task-create-1"

    # Verify in DB
    conn = init_db(db_path)
    task = get_task(conn, task_id_1)
    conn.close()
    assert task is not None
    assert task.name == "CLI Task Create 1"
    assert task.slug == task_slug_1
    assert task.status == TaskStatus.NOT_STARTED
    assert task.description == "Task Desc 1"


def test_task_create_explicit_status(task_cli_runner_env):
    """Test creating a task with an explicit status."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                        '--project', project_slug,
                                        '--name', 'CLI Task Create In Progress',
                                        '--status', 'IN_PROGRESS'])  # Explicit status

    assert result_create.exit_code == 0, f"Output: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    assert response_create["data"]["name"] == "CLI Task Create In Progress"
    assert response_create["data"]["status"] == TaskStatus.IN_PROGRESS.value
    task_id = response_create["data"]["id"]

    # Verify in DB
    conn = init_db(db_path)
    task = get_task(conn, task_id)
    conn.close()
    assert task is not None
    assert task.status == TaskStatus.IN_PROGRESS


def test_task_create_description_from_file(task_cli_runner_env, tmp_path):
    """Test 'task create --description @filepath'."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    desc_content = "Description from file.\nContains newlines.\nAnd symbols: <>?:"
    filepath = tmp_path / "task_desc_create.txt"
    filepath.write_text(desc_content, encoding='utf-8')

    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                  '--project', project_slug,
                                        '--name', 'Task With File Desc Create',
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


def test_task_create_description_from_file_not_found(task_cli_runner_env):
    """Test 'task create --description @filepath' with non-existent file."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    filepath = "no_such_desc_file_create.txt"

    result_create = runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                                  '--project', project_slug,
                                        '--name', 'Task File Not Found Create',
                                        '--description', f"@{filepath}"])

    assert result_create.exit_code != 0  # Should fail
    assert "Error: File not found" in result_create.stderr
    assert filepath in result_create.stderr


def test_task_create_status_case_insensitive(task_cli_runner_env):
    """Test creating tasks with case-insensitive status values."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # 1. Test lowercase status: in_progress
    result_create_lower = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'create', '--project', project_slug, '--name', 'Case Task Lower', '--status', 'in_progress'])
    assert result_create_lower.exit_code == 0, f"Create with lowercase status failed: {result_create_lower.output}"
    response_lower = json.loads(result_create_lower.output)
    assert response_lower['status'] == 'success'
    assert response_lower['data']['status'] == 'IN_PROGRESS', "Status should be stored as uppercase IN_PROGRESS"
    lower_id = response_lower['data']['id']

    # Verify in DB
    with init_db(db_path) as conn:
        task_lower = get_task(conn, lower_id)
        assert task_lower is not None
        assert task_lower.status == TaskStatus.IN_PROGRESS

    # 2. Test mixed-case status: Blocked
    result_create_mixed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'create', '--project', project_slug, '--name', 'Case Task Mixed', '--status', 'Blocked'])
    assert result_create_mixed.exit_code == 0, f"Create with mixed-case status failed: {result_create_mixed.output}"
    response_mixed = json.loads(result_create_mixed.output)
    assert response_mixed['status'] == 'success'
    assert response_mixed['data']['status'] == 'BLOCKED', "Status should be stored as uppercase BLOCKED"
    mixed_id = response_mixed['data']['id']

    # Verify in DB
    with init_db(db_path) as conn:
        task_mixed = get_task(conn, mixed_id)
        assert task_mixed is not None
        assert task_mixed.status == TaskStatus.BLOCKED

    # 3. Test invalid status value (should fail regardless of case)
    result_create_invalid = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'create', '--project', project_slug, '--name', 'Case Task Invalid', '--status', 'invalidStatus'])
    assert result_create_invalid.exit_code != 0, "Create with invalid status should fail"
    # Click's error message for invalid choice
    assert "Invalid value for '--status'" in result_create_invalid.output or "Invalid value for '--status'" in result_create_invalid.stderr

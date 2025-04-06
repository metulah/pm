import json
import uuid
import pytest
from pm.cli.__main__ import cli
from pm.storage import init_db, get_subtask  # For verification
from pm.models import TaskStatus  # For status comparison

# Test successful creation with required name, default status/required


def test_subtask_create_success_defaults(subtask_cli_runner_env):
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]
    subtask_name = "My First Subtask"

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'create', task_id,
        '--name', subtask_name
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert output_data["data"]["task_id"] == task_id
        assert output_data["data"]["name"] == subtask_name
        assert output_data["data"]["description"] is None
        # Default
        assert output_data["data"]["required_for_completion"] is True
        # Default
        assert output_data["data"]["status"] == TaskStatus.NOT_STARTED.value
        subtask_id = output_data["data"]["id"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB
    with init_db(db_path) as conn:
        db_subtask = get_subtask(conn, subtask_id)
        assert db_subtask is not None
        assert db_subtask.task_id == task_id
        assert db_subtask.name == subtask_name
        assert db_subtask.required_for_completion is True
        assert db_subtask.status == TaskStatus.NOT_STARTED


# Test successful creation with all options specified
def test_subtask_create_success_all_options(subtask_cli_runner_env):
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]
    subtask_name = "Detailed Subtask"
    subtask_desc = "A very detailed description"
    target_status = TaskStatus.IN_PROGRESS.value

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'create', task_id,
        '--name', subtask_name,
        '--description', subtask_desc,
        '--optional',  # Set required=False
        '--status', target_status
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert output_data["data"]["task_id"] == task_id
        assert output_data["data"]["name"] == subtask_name
        assert output_data["data"]["description"] == subtask_desc
        # Explicitly optional
        assert output_data["data"]["required_for_completion"] is False
        assert output_data["data"]["status"] == target_status  # Explicitly set
        subtask_id = output_data["data"]["id"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB
    with init_db(db_path) as conn:
        db_subtask = get_subtask(conn, subtask_id)
        assert db_subtask is not None
        assert db_subtask.task_id == task_id
        assert db_subtask.name == subtask_name
        assert db_subtask.description == subtask_desc
        assert db_subtask.required_for_completion is False
        assert db_subtask.status == TaskStatus.IN_PROGRESS


# Test failure when required --name is missing
def test_subtask_create_missing_name(subtask_cli_runner_env):
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'create', task_id,
        # Missing --name
        '--description', "Some desc"
    ])

    assert result.exit_code != 0  # Should fail
    assert "Missing option '--name'" in result.stderr or "Missing option '--name'" in result.output


# Test failure when the target task_id does not exist
def test_subtask_create_task_not_found(subtask_cli_runner_env):
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    non_existent_task_id = str(uuid.uuid4())

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'create', non_existent_task_id,
        '--name', "Subtask For Missing Task"
    ])

    assert result.exit_code == 0  # Command runs, error in JSON
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "error"
        assert "message" in output_data
        # Storage layer raises ValueError for constraint violation
        assert "FOREIGN KEY constraint failed" in output_data[
            "message"] or "Task not found" in output_data["message"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Error parsing JSON error output: {e}\nOutput: {result.output}")

import json
import pytest
from pm.cli.__main__ import cli
from pm.models import TaskStatus  # For status values

# Helper function to create a subtask via CLI for setup


def _create_subtask_cli(runner, db_path, task_id, name, status=None, required=True):
    args = [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'create', task_id,
        '--name', name
    ]
    if status:
        args.extend(['--status', status])
    if not required:
        args.append('--optional')

    result = runner.invoke(cli, args)
    assert result.exit_code == 0, f"Helper failed to create subtask '{name}': {result.output}"
    try:
        return json.loads(result.output)["data"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Helper error parsing subtask create output: {e}\nOutput: {result.output}")

# --- Test Cases ---


def test_subtask_list_empty(subtask_cli_runner_env):
    """Test listing subtasks when the task has none."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'list', task_id
    ])

    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert isinstance(output_data["data"], list)
        assert len(output_data["data"]) == 0  # Expect empty list
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")


def test_subtask_list_multiple_no_filter(subtask_cli_runner_env):
    """Test listing all subtasks when multiple exist."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]

    # Setup: Create subtasks with different statuses
    subtasks_to_create = {
        "Subtask A": TaskStatus.NOT_STARTED.value,
        "Subtask B": TaskStatus.IN_PROGRESS.value,
        "Subtask C": TaskStatus.COMPLETED.value
    }
    created_ids = set()
    for name, status in subtasks_to_create.items():
        data = _create_subtask_cli(
            runner, db_path, task_id, name, status=status)
        created_ids.add(data["id"])

    # Run list command without filter
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'list', task_id
    ])

    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert isinstance(output_data["data"], list)
        assert len(output_data["data"]) == len(
            subtasks_to_create)  # Expect all 3

        listed_ids = {st["id"] for st in output_data["data"]}
        assert listed_ids == created_ids  # Verify all created subtasks are listed
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")


def test_subtask_list_filter_by_status(subtask_cli_runner_env):
    """Test filtering subtasks by status."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]

    # Setup: Create subtasks with different statuses
    _create_subtask_cli(runner, db_path, task_id, "Subtask NS",
                        status=TaskStatus.NOT_STARTED.value)
    in_progress_data = _create_subtask_cli(
        runner, db_path, task_id, "Subtask IP", status=TaskStatus.IN_PROGRESS.value)
    _create_subtask_cli(runner, db_path, task_id,
                        "Subtask Done", status=TaskStatus.COMPLETED.value)
    in_progress_id = in_progress_data["id"]

    # Run list command filtering for IN_PROGRESS
    target_status = TaskStatus.IN_PROGRESS.value
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'list', task_id,
        '--status', target_status
    ])

    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert isinstance(output_data["data"], list)
        assert len(output_data["data"]) == 1  # Expect only the IN_PROGRESS one

        listed_subtask = output_data["data"][0]
        assert listed_subtask["id"] == in_progress_id
        assert listed_subtask["name"] == "Subtask IP"
        assert listed_subtask["status"] == target_status
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")


def test_subtask_list_filter_no_match(subtask_cli_runner_env):
    """Test filtering by a status that matches no subtasks."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]

    # Setup: Create only a NOT_STARTED subtask
    _create_subtask_cli(runner, db_path, task_id,
                        "Subtask Only NS", status=TaskStatus.NOT_STARTED.value)

    # Run list command filtering for BLOCKED (which doesn't exist)
    target_status = TaskStatus.BLOCKED.value
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'list', task_id,
        '--status', target_status
    ])

    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert isinstance(output_data["data"], list)
        assert len(output_data["data"]) == 0  # Expect empty list
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

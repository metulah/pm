import json
import uuid
import pytest
from pm.cli.__main__ import cli
from pm.models import TaskStatus  # For status values

# Helper function to create a subtask via CLI for setup
# (Consider moving to conftest if used across more files)


def _create_subtask_cli(runner, db_path, task_id, name, status=None, required=True, description=None):
    args = [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'create', task_id,
        '--name', name
    ]
    if status:
        args.extend(['--status', status])
    if not required:
        args.append('--optional')
    if description:
        args.extend(['--description', description])

    result = runner.invoke(cli, args)
    assert result.exit_code == 0, f"Helper failed to create subtask '{name}': {result.output}"
    try:
        return json.loads(result.output)["data"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Helper error parsing subtask create output: {e}\nOutput: {result.output}")

# --- Test Cases ---


def test_subtask_show_success(subtask_cli_runner_env):
    """Test showing a subtask that exists."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]

    # Setup: Create a subtask using the CLI helper
    subtask_name = "Showable Subtask"
    subtask_desc = "Description for show"
    subtask_status = TaskStatus.IN_PROGRESS.value
    created_data = _create_subtask_cli(
        runner, db_path, task_id, subtask_name,
        status=subtask_status, required=False, description=subtask_desc
    )
    subtask_id = created_data["id"]

    # Run the show command
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'show', subtask_id
    ])

    # Check output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        # Verify all details match the created subtask
        assert output_data["data"]["id"] == subtask_id
        assert output_data["data"]["task_id"] == task_id
        assert output_data["data"]["name"] == subtask_name
        assert output_data["data"]["description"] == subtask_desc
        assert output_data["data"]["status"] == subtask_status
        assert output_data["data"]["required_for_completion"] is False
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")


def test_subtask_show_not_found(subtask_cli_runner_env):
    """Test showing a subtask ID that does not exist."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    non_existent_id = str(uuid.uuid4())

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'show', non_existent_id
    ])

    # Expect failure status in JSON, check output
    assert result.exit_code == 0  # Command itself runs successfully
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "error"
        assert "message" in output_data
        assert f"Subtask {non_existent_id} not found" in output_data["message"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Error parsing JSON error output: {e}\nOutput: {result.output}")

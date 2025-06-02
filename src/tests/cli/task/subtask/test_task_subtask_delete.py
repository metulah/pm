import json
import uuid
import pytest
from pm.cli.__main__ import cli
from pm.storage import init_db, get_subtask  # For verification

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


def test_subtask_delete_success(subtask_cli_runner_env):
    """Test deleting a subtask that exists."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]

    # Setup: Create a subtask using the CLI helper
    subtask_name = "Subtask To Delete"
    created_data = _create_subtask_cli(runner, db_path, task_id, subtask_name)
    subtask_id = created_data["id"]

    # Verify it exists in DB before delete
    with init_db(db_path) as conn:
        assert get_subtask(conn, subtask_id) is not None

    # Run the delete command
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'delete', subtask_id
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "message" in output_data
        assert f"Subtask {subtask_id} deleted" in output_data["message"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify it's gone from DB
    with init_db(db_path) as conn:
        assert get_subtask(conn, subtask_id) is None


def test_subtask_delete_not_found(subtask_cli_runner_env):
    """Test deleting a subtask ID that does not exist."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    non_existent_id = str(uuid.uuid4())

    # Verify it doesn't exist first (optional sanity check)
    with init_db(db_path) as conn:
        assert get_subtask(conn, non_existent_id) is None

    # Run the delete command
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'delete', non_existent_id
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

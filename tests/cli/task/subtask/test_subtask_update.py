import json
import uuid
import pytest
from pm.cli.__main__ import cli
from pm.storage import init_db, get_subtask  # For verification
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


def test_subtask_update_name(subtask_cli_runner_env):
    """Test updating only the subtask name."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]

    # Setup: Create a subtask
    original_name = "Original Name"
    created_data = _create_subtask_cli(runner, db_path, task_id, original_name)
    subtask_id = created_data["id"]

    # Run the update command
    new_name = "Updated Subtask Name"
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'update', subtask_id,
        '--name', new_name
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert output_data["data"]["id"] == subtask_id
        assert output_data["data"]["name"] == new_name  # Verify new name
        # Verify others unchanged
        assert output_data["data"]["description"] is None
        assert output_data["data"]["status"] == TaskStatus.NOT_STARTED.value
        assert output_data["data"]["required_for_completion"] is True
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB
    with init_db(db_path) as conn:
        db_subtask = get_subtask(conn, subtask_id)
        assert db_subtask is not None
        assert db_subtask.name == new_name


def test_subtask_update_status_and_optional(subtask_cli_runner_env):
    """Test updating status and required flag simultaneously."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]

    # Setup: Create a subtask (default: required, not_started)
    subtask_name = "Status Optional Update"
    created_data = _create_subtask_cli(runner, db_path, task_id, subtask_name)
    subtask_id = created_data["id"]

    # Run the update command
    new_status = TaskStatus.COMPLETED.value
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'update', subtask_id,
        '--status', new_status,
        '--optional'  # Change required to False
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert output_data["data"]["id"] == subtask_id
        assert output_data["data"]["name"] == subtask_name  # Unchanged
        assert output_data["data"]["status"] == new_status  # Updated
        # Updated
        assert output_data["data"]["required_for_completion"] is False
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB
    with init_db(db_path) as conn:
        db_subtask = get_subtask(conn, subtask_id)
        assert db_subtask is not None
        assert db_subtask.status == TaskStatus.COMPLETED
        assert db_subtask.required_for_completion is False


def test_subtask_update_description(subtask_cli_runner_env):
    """Test updating only the description."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]

    # Setup: Create a subtask without description
    subtask_name = "Desc Update Test"
    created_data = _create_subtask_cli(runner, db_path, task_id, subtask_name)
    subtask_id = created_data["id"]
    assert created_data["description"] is None

    # Run the update command
    new_description = "This is the new description."
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'update', subtask_id,
        '--description', new_description
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert output_data["data"]["id"] == subtask_id
        # Verify new description
        assert output_data["data"]["description"] == new_description
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB
    with init_db(db_path) as conn:
        db_subtask = get_subtask(conn, subtask_id)
        assert db_subtask is not None
        assert db_subtask.description == new_description


def test_subtask_update_not_found(subtask_cli_runner_env):
    """Test updating a subtask ID that does not exist."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    non_existent_id = str(uuid.uuid4())

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'update', non_existent_id,
        '--name', "New Name For Missing"
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


def test_subtask_update_no_options(subtask_cli_runner_env):
    """Test calling update with no options - should succeed but change nothing."""
    runner, db_path, project_info, task_info = subtask_cli_runner_env
    task_id = task_info["task_id"]

    # Setup: Create a subtask
    original_name = "No Opts Update"
    original_desc = "Original Desc"
    original_status = TaskStatus.NOT_STARTED.value
    original_required = True
    created_data = _create_subtask_cli(
        runner, db_path, task_id, original_name,
        status=original_status, required=original_required, description=original_desc
    )
    subtask_id = created_data["id"]

    # Run the update command with no update options
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'subtask', 'update', subtask_id
    ])

    # Check CLI output - should return the current state
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert output_data["data"]["id"] == subtask_id
        assert output_data["data"]["name"] == original_name
        assert output_data["data"]["description"] == original_desc
        assert output_data["data"]["status"] == original_status
        assert output_data["data"]["required_for_completion"] == original_required
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB (nothing should have changed)
    with init_db(db_path) as conn:
        db_subtask = get_subtask(conn, subtask_id)
        assert db_subtask is not None
        assert db_subtask.name == original_name
        assert db_subtask.description == original_desc
        assert db_subtask.status.value == original_status
        assert db_subtask.required_for_completion == original_required

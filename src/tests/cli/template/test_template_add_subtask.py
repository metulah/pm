import json
import uuid
import pytest
from pm.cli.__main__ import cli
# For verification
from pm.storage import init_db, get_subtask_template

# Helper function to create a template via CLI for setup


def _create_template_cli(runner, db_path, name, description=None):
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'template', 'create', '--name', name,
        *(['--description', description] if description else [])
    ])
    assert result.exit_code == 0, f"Helper failed to create template '{name}': {result.output}"
    try:
        return json.loads(result.output)["data"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Helper error parsing template create output: {e}\nOutput: {result.output}")

# --- Test Cases ---


def test_template_add_subtask_success_required(cli_runner_env):
    """Test adding a required subtask (default)."""
    runner, db_path = cli_runner_env
    template_data = _create_template_cli(
        runner, db_path, "Template For Subtasks")
    template_id = template_data["id"]
    subtask_name = "Required Subtask"
    subtask_desc = "Desc for required"

    # Run the add-subtask command (default is --required)
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'template', 'add-subtask', template_id,
        '--name', subtask_name,
        '--description', subtask_desc
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert output_data["data"]["template_id"] == template_id
        assert output_data["data"]["name"] == subtask_name
        assert output_data["data"]["description"] == subtask_desc
        # Default
        assert output_data["data"]["required_for_completion"] is True
        subtask_id = output_data["data"]["id"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB
    with init_db(db_path) as conn:
        db_subtask = get_subtask_template(conn, subtask_id)
        assert db_subtask is not None
        assert db_subtask.template_id == template_id
        assert db_subtask.name == subtask_name
        assert db_subtask.required_for_completion is True


def test_template_add_subtask_success_optional(cli_runner_env):
    """Test adding an optional subtask using --optional flag."""
    runner, db_path = cli_runner_env
    template_data = _create_template_cli(
        runner, db_path, "Template For Optional Subtask")
    template_id = template_data["id"]
    subtask_name = "Optional Subtask"

    # Run the add-subtask command with --optional
    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'template', 'add-subtask', template_id,
        '--name', subtask_name,
        '--optional'  # Explicitly set as optional
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert output_data["data"]["template_id"] == template_id
        assert output_data["data"]["name"] == subtask_name
        # No description provided
        assert output_data["data"]["description"] is None
        # Should be False
        assert output_data["data"]["required_for_completion"] is False
        subtask_id = output_data["data"]["id"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB
    with init_db(db_path) as conn:
        db_subtask = get_subtask_template(conn, subtask_id)
        assert db_subtask is not None
        assert db_subtask.template_id == template_id
        assert db_subtask.name == subtask_name
        assert db_subtask.required_for_completion is False


def test_template_add_subtask_missing_name(cli_runner_env):
    """Test failure when required --name is missing."""
    runner, db_path = cli_runner_env
    template_data = _create_template_cli(
        runner, db_path, "Template Missing Name")
    template_id = template_data["id"]

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'template', 'add-subtask', template_id,
        # Missing --name
        '--description', "Some desc"
    ])

    assert result.exit_code != 0  # Should fail
    assert "Missing option '--name'" in result.stderr or "Missing option '--name'" in result.output


def test_template_add_subtask_template_not_found(cli_runner_env):
    """Test failure when the target template_id does not exist."""
    runner, db_path = cli_runner_env
    non_existent_template_id = str(uuid.uuid4())

    result = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'template', 'add-subtask', non_existent_template_id,
        '--name', "Subtask For Missing Template"
    ])

    assert result.exit_code == 0  # Command runs, error in JSON
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "error"
        assert "message" in output_data
        # The storage layer raises ValueError for constraint violation
        # Adjust based on actual error
        assert "FOREIGN KEY constraint failed" in output_data[
            "message"] or "Template not found" in output_data["message"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Error parsing JSON error output: {e}\nOutput: {result.output}")

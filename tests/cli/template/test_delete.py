import json
import uuid
import pytest
from pm.cli.__main__ import cli
from pm.storage import init_db, get_task_template  # For verification

# Helper function to create a template via CLI for setup
# (Consider moving to conftest if used across more files)


def _create_template_cli(runner, db_path, name, description=None):
    result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',
        'template', 'create',
        '--name', name,
        *(['--description', description] if description else [])
    ])
    assert result.exit_code == 0, f"Helper failed to create template '{name}': {result.output}"
    try:
        return json.loads(result.output)["data"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Helper error parsing create output for '{name}': {e}\nOutput: {result.output}")

# Test deleting a template that exists


def test_template_delete_success(cli_runner_env):
    runner, db_path = cli_runner_env
    template_name = "Template To Delete"

    # Setup: Create the template using the CLI helper
    created_template_data = _create_template_cli(
        runner, db_path, template_name)
    template_id = created_template_data["id"]

    # Verify it exists in DB before delete
    with init_db(db_path) as conn:
        assert get_task_template(conn, template_id) is not None

    # Run the delete command
    result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',
        'template', 'delete', template_id
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "message" in output_data
        assert f"Template {template_id} deleted" in output_data["message"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify it's gone from DB
    with init_db(db_path) as conn:
        assert get_task_template(conn, template_id) is None


# Test deleting a template ID that does not exist
def test_template_delete_not_found(cli_runner_env):
    runner, db_path = cli_runner_env
    non_existent_id = str(uuid.uuid4())

    # Verify it doesn't exist first (optional sanity check)
    with init_db(db_path) as conn:
        assert get_task_template(conn, non_existent_id) is None

    # Run the delete command
    result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',
        'template', 'delete', non_existent_id
    ])

    # Expect failure status in JSON, check output
    assert result.exit_code == 0  # Command itself runs successfully
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "error"
        assert "message" in output_data
        assert f"Template {non_existent_id} not found" in output_data["message"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Error parsing JSON error output: {e}\nOutput: {result.output}")

import json
import pytest
from pm.cli.__main__ import cli  # Align import with project tests
# Import storage functions for verification
from pm.storage import init_db, get_task_template, list_task_templates

# Test successful creation with name and description


def test_template_create_success(cli_runner_env):
    runner, db_path = cli_runner_env
    template_name = "My Test Template"
    template_desc = "A description for the test template"

    # Verify DB is empty initially (optional but good practice)
    with init_db(db_path) as conn:
        assert len(list_task_templates(conn)) == 0

    # Invoke CLI command
    result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',  # Explicitly request JSON
        'template', 'create',
        '--name', template_name,
        '--description', template_desc
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert output_data["data"]["name"] == template_name
        assert output_data["data"]["description"] == template_desc
        assert "id" in output_data["data"]
        template_id = output_data["data"]["id"]  # Get ID for DB verification
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB
    with init_db(db_path) as conn:
        db_template = get_task_template(conn, template_id)
        assert db_template is not None
        assert db_template.id == template_id
        assert db_template.name == template_name
        assert db_template.description == template_desc


# Test successful creation with only the required name
def test_template_create_success_name_only(cli_runner_env):
    runner, db_path = cli_runner_env
    template_name = "Name Only Template"

    result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',  # Explicitly request JSON
        'template', 'create',
        '--name', template_name
    ])

    # Check CLI output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert output_data["data"]["name"] == template_name
        # Description should be None
        assert output_data["data"]["description"] is None
        assert "id" in output_data["data"]
        template_id = output_data["data"]["id"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

    # Verify directly in DB
    with init_db(db_path) as conn:
        db_template = get_task_template(conn, template_id)
        assert db_template is not None
        assert db_template.id == template_id
        assert db_template.name == template_name
        assert db_template.description is None


# Test failure when the required --name option is missing
def test_template_create_missing_name(cli_runner_env):
    runner, db_path = cli_runner_env

    result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',
        'template', 'create',
        '--description', "Some description"  # Provide description but no name
    ])

    assert result.exit_code != 0  # Should fail
    # Click typically outputs error messages to stderr, but CliRunner might capture it in stdout if mix_stderr=False wasn't set (it is in our fixture)
    # Check stderr first, then stdout as fallback
    assert "Missing option '--name'" in result.stderr or "Missing option '--name'" in result.output

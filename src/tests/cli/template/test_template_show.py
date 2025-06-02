import json
import uuid
import pytest
from pm.cli.__main__ import cli
from pm.models import SubtaskTemplate
from pm.storage import init_db, create_subtask_template  # For subtask setup

# Helper function to create a template via CLI for setup


def _create_template_cli(runner, db_path, name, description=None):
    result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',
        'template', 'create',
        '--name', name,
        *(['--description', description] if description else [])
    ])
    assert result.exit_code == 0, f"Failed to create template '{name}': {result.output}"
    try:
        return json.loads(result.output)["data"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Error parsing create output for '{name}': {e}\nOutput: {result.output}")

# Test showing a template that exists (no subtasks)


def test_template_show_exists_no_subtasks(cli_runner_env):
    runner, db_path = cli_runner_env
    template_name = "Showable Template"
    template_desc = "Description for show"

    # Setup: Create the template using the CLI
    created_template_data = _create_template_cli(
        runner, db_path, template_name, template_desc)
    template_id = created_template_data["id"]

    # Run the show command
    result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',
        'template', 'show', template_id
    ])

    # Check output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert output_data["data"]["id"] == template_id
        assert output_data["data"]["name"] == template_name
        assert output_data["data"]["description"] == template_desc
        assert "subtasks" in output_data["data"]
        assert isinstance(output_data["data"]["subtasks"], list)
        assert len(output_data["data"]["subtasks"]) == 0  # Expect no subtasks
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")

# Test showing a template that exists and has subtasks


def test_template_show_exists_with_subtasks(cli_runner_env):
    runner, db_path = cli_runner_env
    template_name = "Template With Subtasks"

    # Setup: Create the template using the CLI
    created_template_data = _create_template_cli(
        runner, db_path, template_name)
    template_id = created_template_data["id"]

    # Setup: Create subtasks directly via storage (simpler for now)
    subtask_names = ["Subtask One", "Subtask Two"]
    created_subtask_ids = set()
    with init_db(db_path) as conn:
        for name in subtask_names:
            subtask = SubtaskTemplate(
                id=str(uuid.uuid4()),
                template_id=template_id,
                name=name,
                description=f"Desc for {name}",
                required_for_completion=True
            )
            created = create_subtask_template(conn, subtask)
            created_subtask_ids.add(created.id)

    # Run the show command
    result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',
        'template', 'show', template_id
    ])

    # Check output
    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert output_data["data"]["id"] == template_id
        assert output_data["data"]["name"] == template_name
        assert "subtasks" in output_data["data"]
        assert isinstance(output_data["data"]["subtasks"], list)
        assert len(output_data["data"]["subtasks"]) == len(
            subtask_names)  # Expect subtasks

        # Verify subtask details
        listed_subtask_ids = {st["id"]
                              for st in output_data["data"]["subtasks"]}
        assert listed_subtask_ids == created_subtask_ids
        subtask_one = next(
            (st for st in output_data["data"]["subtasks"] if st["name"] == "Subtask One"), None)
        assert subtask_one is not None
        assert subtask_one["description"] == "Desc for Subtask One"
        assert subtask_one["required_for_completion"] is True

    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")


# Test showing a template ID that does not exist
def test_template_show_not_found(cli_runner_env):
    runner, db_path = cli_runner_env
    non_existent_id = str(uuid.uuid4())

    result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',
        'template', 'show', non_existent_id
    ])

    # Expect failure, check output
    assert result.exit_code == 0  # Command succeeds but returns error status in JSON
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "error"
        assert "message" in output_data
        assert f"Template {non_existent_id} not found" in output_data["message"]
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Error parsing JSON error output: {e}\nOutput: {result.output}")

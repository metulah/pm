import json
import pytest
from pm.cli.__main__ import cli  # Align import

# Test listing when no templates exist


def test_template_list_empty(cli_runner_env):
    runner, db_path = cli_runner_env

    result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',  # Explicit format
        'template', 'list'
    ])

    assert result.exit_code == 0, f"CLI Error: {result.output}"
    try:
        output_data = json.loads(result.output)
        assert output_data["status"] == "success"
        assert "data" in output_data
        assert isinstance(output_data["data"], list)
        assert len(output_data["data"]) == 0  # Expect an empty list
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(f"Error parsing JSON output: {e}\nOutput: {result.output}")


# Test listing when multiple templates exist
def test_template_list_multiple(cli_runner_env):
    runner, db_path = cli_runner_env

    # Setup: Create templates using the CLI 'create' command
    template_details = {
        "Template Alpha": "Desc Alpha",
        "Template Beta": "Desc Beta",
        "Template Gamma": "Desc Gamma"
    }
    created_ids = set()

    for name, desc in template_details.items():
        create_result = runner.invoke(cli, [
            '--db-path', db_path,
            '--format', 'json',
            'template', 'create',
            '--name', name,
            '--description', desc
        ])
        assert create_result.exit_code == 0, f"Failed to create template '{name}': {create_result.output}"
        try:
            create_output = json.loads(create_result.output)
            created_ids.add(create_output["data"]["id"])
        except (json.JSONDecodeError, KeyError) as e:
            pytest.fail(
                f"Error parsing create output for '{name}': {e}\nOutput: {create_result.output}")

    assert len(created_ids) == len(
        template_details), "Failed to create all test templates"

    # Run the list command
    list_result = runner.invoke(cli, [
        '--db-path', db_path,
        '--format', 'json',  # Explicit format
        'template', 'list'
    ])

    assert list_result.exit_code == 0, f"CLI Error: {list_result.output}"
    try:
        list_output_data = json.loads(list_result.output)
        assert list_output_data["status"] == "success"
        assert "data" in list_output_data
        assert isinstance(list_output_data["data"], list)
        assert len(list_output_data["data"]) == len(
            template_details)  # Check count

        # Verify the listed templates match the ones created
        listed_ids = {item["id"] for item in list_output_data["data"]}
        assert listed_ids == created_ids

        # Optional: Spot-check one template's details
        beta_template = next(
            (t for t in list_output_data["data"] if t["name"] == "Template Beta"), None)
        assert beta_template is not None
        assert beta_template["description"] == "Desc Beta"

    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Error parsing list JSON output: {e}\nOutput: {list_result.output}")

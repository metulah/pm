import pytest
import json
from pm.cli.__main__ import cli

# Fixture defined locally as conftest import is problematic


@pytest.fixture(scope="function")  # Use function scope for isolation
def metadata_test_setup(task_cli_runner_env):
    """
    Sets up a specific task for metadata tests within the default project.
    Yields runner, db_path, project_info, task_id, and task_slug.
    """
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create a specific task for metadata tests
    task_name = "CLI Metadata Test Task"
    # Use a predictable slug based on the name
    expected_task_slug = "cli-metadata-test-task"
    result_task = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                      '--project', project_slug, '--name', task_name])

    if result_task.exit_code != 0:
        pytest.fail(
            f"Failed to create task for metadata tests: {result_task.output}")

    try:
        task_data = json.loads(result_task.output)['data']
        task_id = task_data['id']
        task_slug = task_data['slug']
        # Verify slug matches prediction - important for tests relying on slug
        assert task_slug == expected_task_slug, f"Expected slug '{expected_task_slug}' but got '{task_slug}'"
    except (json.JSONDecodeError, KeyError, AssertionError) as e:
        pytest.fail(
            f"Failed to parse task creation output or verify slug: {e}\nOutput: {result_task.output}")

    yield runner, db_path, project_info, task_id, task_slug


def test_metadata_set_string(metadata_test_setup):
    """Test setting string metadata."""
    runner, db_path, project_info, task_id, task_slug = metadata_test_setup

    key = "status_meta_set"
    value = "in-progress-set-test"

    result_set_str = runner.invoke(
        # Use task_id
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'metadata', 'set', task_id, '--key', key, '--value', value])
    assert result_set_str.exit_code == 0, f"Output: {result_set_str.output}"
    response_set_str = json.loads(result_set_str.output)
    assert response_set_str["status"] == "success"
    assert response_set_str["data"]["key"] == key
    assert response_set_str["data"]["value"] == value
    # Value type is not returned by 'set'


def test_metadata_set_int(metadata_test_setup):
    """Test setting integer metadata with explicit type."""
    runner, db_path, project_info, task_id, task_slug = metadata_test_setup

    key = "priority_meta_set"
    value_str = "5"
    value_int = 5

    result_set_int = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'metadata', 'set', task_id, '--key', key, '--value', value_str, '--type', 'int'])  # Use task_id
    assert result_set_int.exit_code == 0, f"Output: {result_set_int.output}"
    response_set_int = json.loads(result_set_int.output)
    assert response_set_int["status"] == "success"
    assert response_set_int["data"]["key"] == key
    # Should be parsed as int
    assert response_set_int["data"]["value"] == value_int
    # Value type is not returned by 'set'


def test_metadata_set_overwrite(metadata_test_setup):
    """Test overwriting existing metadata."""
    runner, db_path, project_info, task_id, task_slug = metadata_test_setup
    key = "overwrite_meta"

    # Set initial value
    runner.invoke(cli, ['--db-path', db_path, 'task', 'metadata',
                  'set', task_id, '--key', key, '--value', 'initial'])

    # Overwrite with new value
    result_overwrite = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'metadata', 'set', task_id, '--key', key, '--value', 'overwritten'])
    assert result_overwrite.exit_code == 0
    response_overwrite = json.loads(result_overwrite.output)
    assert response_overwrite["status"] == "success"
    assert response_overwrite["data"]["value"] == "overwritten"

    # Verify using get command
    result_get = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'metadata', 'get', task_id, '--key', key])
    response_get = json.loads(result_get.output)
    assert response_get["data"][0]["value"] == "overwritten"

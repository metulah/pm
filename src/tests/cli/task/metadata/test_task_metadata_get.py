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


def test_metadata_get_specific(metadata_test_setup):
    """Test getting specific metadata key."""
    runner, db_path, project_info, task_id, task_slug = metadata_test_setup
    key_str = "status_meta_get"
    value_str = "in-progress-get-test"
    key_int = "priority_meta_get"
    value_int_str = "10"
    value_int = 10

    # Set metadata first
    runner.invoke(cli, ['--db-path', db_path, 'task', 'metadata',
                  'set', task_id, '--key', key_str, '--value', value_str])
    runner.invoke(cli, ['--db-path', db_path, 'task', 'metadata', 'set',
                  task_id, '--key', key_int, '--value', value_int_str, '--type', 'int'])

    # Test getting specific metadata (string)
    result_get_str = runner.invoke(
        # Use task_id
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'metadata', 'get', task_id, '--key', key_str])
    assert result_get_str.exit_code == 0
    response_get_str = json.loads(result_get_str.output)
    assert response_get_str["status"] == "success"
    assert len(response_get_str["data"]) == 1
    assert response_get_str["data"][0]["key"] == key_str
    assert response_get_str["data"][0]["value"] == value_str
    # Verify type on get
    assert response_get_str["data"][0]["type"] == "string"

    # Test getting specific metadata (int)
    result_get_int = runner.invoke(
        # Use task_id
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'metadata', 'get', task_id, '--key', key_int])
    assert result_get_int.exit_code == 0
    response_get_int = json.loads(result_get_int.output)
    assert response_get_int["status"] == "success"
    assert len(response_get_int["data"]) == 1
    assert response_get_int["data"][0]["key"] == key_int
    assert response_get_int["data"][0]["value"] == value_int
    assert response_get_int["data"][0]["type"] == "int"  # Verify type on get


def test_metadata_get_all(metadata_test_setup):
    """Test getting all metadata for a task."""
    runner, db_path, project_info, task_id, task_slug = metadata_test_setup
    key1 = "meta_get_all_1"
    value1 = "value_get_1"
    key2 = "meta_get_all_2"
    value2_str = "99"
    value2_int = 99

    # Set metadata first
    runner.invoke(cli, ['--db-path', db_path, 'task', 'metadata',
                  'set', task_id, '--key', key1, '--value', value1])
    runner.invoke(cli, ['--db-path', db_path, 'task', 'metadata', 'set',
                  task_id, '--key', key2, '--value', value2_str, '--type', 'int'])

    # Test getting all metadata for the task
    result_get_all = runner.invoke(
        # Use task_id
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'metadata', 'get', task_id])
    assert result_get_all.exit_code == 0
    response_get_all = json.loads(result_get_all.output)
    assert response_get_all["status"] == "success"
    assert len(response_get_all["data"]) == 2
    keys_found = {item['key'] for item in response_get_all["data"]}
    values_found = {item['value'] for item in response_get_all["data"]}
    assert keys_found == {key1, key2}
    assert values_found == {value1, value2_int}


def test_metadata_get_nonexistent(metadata_test_setup):
    """Test getting a non-existent metadata key."""
    runner, db_path, project_info, task_id, task_slug = metadata_test_setup
    non_existent_key = "no_such_meta_key"

    result_get = runner.invoke(
        # Use task_id
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'metadata', 'get', task_id, '--key', non_existent_key])
    assert result_get.exit_code == 0
    response_get = json.loads(result_get.output)
    assert response_get["status"] == "success"  # Command succeeds
    assert len(response_get["data"]) == 0  # But returns empty list

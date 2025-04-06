import pytest
import json
from pm.cli.__main__ import cli

# Import the fixture from the parent task directory's conftest
# Pytest automatically discovers fixtures in parent conftest.py files,
# so direct import might not be strictly necessary, but makes dependency clear.
# from ..conftest import task_cli_runner_env # This relative import might not work depending on pytest path handling, rely on discovery.


@pytest.fixture(scope="function")
# Depend on the fixture from parent conftest
def subtask_cli_runner_env(task_cli_runner_env):
    """
    Fixture providing CliRunner, db_path, a default project,
    and a default task within that project for subtask CLI tests.
    """
    runner, db_path, project_info = task_cli_runner_env
    project_id = project_info["project_id"]

    # Create a default task within the default project
    task_name = "Default Subtask Test Task"
    result_task = runner.invoke(cli, [
        '--db-path', db_path, '--format', 'json',
        'task', 'create', '--project', project_id, '--name', task_name
    ])

    if result_task.exit_code != 0:
        pytest.fail(
            f"Failed to create default task for subtask tests: {result_task.output}")

    try:
        task_data = json.loads(result_task.output)['data']
        task_id = task_data['id']
        task_slug = task_data['slug']
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Failed to parse task creation output: {e}\nOutput: {result_task.output}")

    task_info = {"task_id": task_id,
                 "task_slug": task_slug, "task_name": task_name}

    # Yield runner, db_path, project_info, and task_info
    yield runner, db_path, project_info, task_info

    # Cleanup is handled by task_cli_runner_env and tmp_path_factory

import pytest
import json
from click.testing import CliRunner

from pm.storage import init_db
from pm.cli.__main__ import cli


@pytest.fixture(scope="function")  # Use function scope for test isolation
def task_cli_runner_env(tmp_path_factory):
    """
    Fixture providing a CliRunner, a temporary db_path,
    and a pre-created project for task CLI tests.
    Uses session scope for efficiency as the DB setup is the same for all task tests.
    """
    # Create a single DB for the whole session
    db_path = str(tmp_path_factory.mktemp("task_tests_db") / "test_tasks.db")
    conn = init_db(db_path)
    conn.close()
    runner = CliRunner(mix_stderr=False)

    # Create a default project using the CLI
    project_name = "Default Task Test Project"
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', project_name])

    if result_proj.exit_code != 0:
        pytest.fail(
            f"Failed to create default project for task tests: {result_proj.output}")

    try:
        project_data = json.loads(result_proj.output)['data']
        project_slug = project_data['slug']
        project_id = project_data['id']
    except (json.JSONDecodeError, KeyError) as e:
        pytest.fail(
            f"Failed to parse project creation output: {e}\nOutput: {result_proj.output}")

    # Yield runner, db_path, and project identifiers
    yield runner, db_path, {"project_id": project_id, "project_slug": project_slug, "project_name": project_name}

    # Cleanup (tmp_path_factory handles directory removal)

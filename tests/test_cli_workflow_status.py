"""Tests for CLI command workflows related to status transitions."""

import pytest
import json
from pm.storage import init_db
from pm.cli import cli
from click.testing import CliRunner

# --- Fixture for CLI Runner and DB Path ---


@pytest.fixture
def cli_runner_env(tmp_path):
    """Fixture providing a CliRunner and a temporary db_path."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)  # Initialize the db file
    conn.close()  # Close initial connection
    runner = CliRunner(mix_stderr=False)  # Don't mix stdout/stderr
    return runner, db_path

# --- Status Workflow Tests ---


def test_project_status_transitions(cli_runner_env):
    """Test valid and invalid project status transitions."""
    runner, db_path = cli_runner_env

    # 1. Create an ACTIVE project
    result_active = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'create',
                                        '--name', 'Transition Test Proj'])
    proj_data = json.loads(result_active.output)['data']
    proj_slug = proj_data['slug']
    assert proj_data['status'] == 'PROSPECTIVE'  # Default is now PROSPECTIVE

    # 2. Test invalid transition: PROSPECTIVE -> ARCHIVED (should fail)
    # Project starts as PROSPECTIVE now
    result_invalid_1 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                           proj_slug, '--status', 'ARCHIVED'])
    assert result_invalid_1.exit_code == 1  # CLI should exit with error code
    assert "Error: Invalid project status transition: PROSPECTIVE -> ARCHIVED" in result_invalid_1.stderr  # Check stderr

    # 3. Test invalid transition: ACTIVE -> COMPLETED (with incomplete task)
    # First, transition the project PROSPECTIVE -> ACTIVE
    result_make_active = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                             proj_slug, '--status', 'ACTIVE'])
    assert result_make_active.exit_code == 0, "Failed to make project ACTIVE first"
    assert json.loads(result_make_active.output)['data']['status'] == 'ACTIVE'

    # Now create an incomplete task
    runner.invoke(cli, ['--db-path', db_path, 'task', 'create', '--project', proj_slug,
                        '--name', 'Incomplete Task', '--status', 'IN_PROGRESS'])

    # Now attempt the invalid ACTIVE -> COMPLETED transition
    result_invalid_comp = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                              proj_slug, '--status', 'COMPLETED'])
    assert result_invalid_comp.exit_code == 1  # CLI should exit with error code
    assert "Error: Cannot mark project as COMPLETED" in result_invalid_comp.stderr  # Check stderr
    # Check stderr
    assert "'Incomplete Task' (IN_PROGRESS)" in result_invalid_comp.stderr

    # 3b. Complete the task
    runner.invoke(cli, ['--db-path', db_path, 'task', 'update', proj_slug, 'incomplete-task',
                        '--status', 'COMPLETED'])

    # 3c. Test valid transition: ACTIVE -> COMPLETED (now that task is complete)
    result_valid_1 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                         proj_slug, '--status', 'COMPLETED'])
    assert result_valid_1.exit_code == 0
    assert json.loads(result_valid_1.output)['status'] == 'success'
    assert json.loads(result_valid_1.output)['data']['status'] == 'COMPLETED'

    # 4. Test invalid transition: COMPLETED -> ACTIVE (not currently allowed)
    result_invalid_2 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                           proj_slug, '--status', 'ACTIVE'])
    assert result_invalid_2.exit_code == 1  # CLI should exit with error code
    assert "Error: Invalid project status transition: COMPLETED -> ACTIVE" in result_invalid_2.stderr  # Check stderr

    # 5. Test valid transition: COMPLETED -> ARCHIVED
    result_valid_2 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                         proj_slug, '--status', 'ARCHIVED'])
    assert result_valid_2.exit_code == 0
    assert json.loads(result_valid_2.output)['status'] == 'success'
    assert json.loads(result_valid_2.output)['data']['status'] == 'ARCHIVED'

    # 6. Test invalid transition: ARCHIVED -> COMPLETED (not currently allowed)
    result_invalid_3 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                           proj_slug, '--status', 'COMPLETED'])
    assert result_invalid_3.exit_code == 1  # CLI should exit with error code
    assert "Error: Invalid project status transition: ARCHIVED -> COMPLETED" in result_invalid_3.stderr  # Check stderr

    # 7. Create another ACTIVE project for CANCELLED test
    result_active_2 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'create',
                                          '--name', 'Cancel Test Proj'])
    proj_data_2 = json.loads(result_active_2.output)['data']
    proj_slug_2 = proj_data_2['slug']

    # 8. Test valid transition: ACTIVE -> CANCELLED
    result_valid_3 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                         proj_slug_2, '--status', 'CANCELLED'])
    assert result_valid_3.exit_code == 0
    assert json.loads(result_valid_3.output)['status'] == 'success'
    assert json.loads(result_valid_3.output)['data']['status'] == 'CANCELLED'

    # 9. Test valid transition: CANCELLED -> ARCHIVED
    result_valid_4 = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                         proj_slug_2, '--status', 'ARCHIVED'])
    assert result_valid_4.exit_code == 0
    assert json.loads(result_valid_4.output)['status'] == 'success'
    assert json.loads(result_valid_4.output)['data']['status'] == 'ARCHIVED'

import json
from pm.storage import init_db, get_project, get_project_by_slug
from pm.cli.__main__ import cli


# --- Deletion Tests ---

def test_project_delete_requires_force(cli_runner_env):
    """Test that 'project delete' fails without --force."""
    runner, db_path = cli_runner_env
    # Setup: Create a project
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Force Delete Test'])
    assert result_create.exit_code == 0
    project_slug = json.loads(result_create.output)['data']['slug']

    # Attempt delete without --force
    result_delete = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_slug])

    # Expect failure (non-zero exit code) and specific error message
    assert result_delete.exit_code != 0
    assert "Error: Deleting a project is irreversible" in result_delete.stderr
    assert "--force" in result_delete.stderr

    # Verify project still exists
    conn = init_db(db_path)
    # Use get_project_by_slug for verification
    project = get_project_by_slug(conn, project_slug)
    conn.close()
    assert project is not None


def test_project_delete_with_force(cli_runner_env):
    """Test that 'project delete' succeeds with --force."""
    runner, db_path = cli_runner_env
    # Setup: Create a project
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Force Delete Success'])
    assert result_create.exit_code == 0
    project_slug = json.loads(result_create.output)['data']['slug']
    project_id = json.loads(result_create.output)[
        'data']['id']  # Need ID for final check

    # Attempt delete with --force
    result_delete = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'delete', project_slug, '--force'])

    # Expect success
    assert result_delete.exit_code == 0
    response = json.loads(result_delete.output)
    assert response['status'] == 'success'
    assert f"Project '{project_slug}' deleted" in response['message']

    # Verify project is gone
    conn = init_db(db_path)
    project = get_project(conn, project_id)  # Check by ID
    conn.close()
    assert project is None

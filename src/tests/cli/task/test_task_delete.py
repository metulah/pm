import json
from pm.storage import init_db, get_task
from pm.cli.__main__ import cli


def test_task_delete_requires_force(task_cli_runner_env):
    """Test that 'task delete' fails without --force."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create a task first
    task_name = "Delete Force Test Task"
    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                        '--project', project_slug, '--name', task_name])
    assert result_create.exit_code == 0
    task_slug = json.loads(result_create.output)['data']['slug']
    task_id = json.loads(result_create.output)['data']['id']

    # Attempt delete without --force
    result_delete = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'delete', project_slug, task_slug])

    # Expect failure and specific error message
    assert result_delete.exit_code != 0
    assert "Error: Deleting a task is irreversible" in result_delete.stderr
    assert "--force" in result_delete.stderr

    # Verify task still exists
    conn = init_db(db_path)
    task = get_task(conn, task_id)
    conn.close()
    assert task is not None


def test_task_delete_with_force(task_cli_runner_env):
    """Test that 'task delete' succeeds with --force."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create a task first
    task_name = "Delete Force Success Task"
    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                        '--project', project_slug, '--name', task_name])
    assert result_create.exit_code == 0
    task_slug = json.loads(result_create.output)['data']['slug']
    task_id = json.loads(result_create.output)['data']['id']

    # Attempt delete with --force
    result_delete = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'delete', project_slug, task_slug, '--force'])

    # Expect success
    assert result_delete.exit_code == 0
    response = json.loads(result_delete.output)
    assert response['status'] == 'success'
    assert f"Task '{task_slug}' deleted" in response['message']

    # Verify task is gone
    conn = init_db(db_path)
    task = get_task(conn, task_id)
    conn.close()
    assert task is None

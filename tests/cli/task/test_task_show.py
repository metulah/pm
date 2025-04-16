import json
from pm.cli.__main__ import cli


def test_task_show_basic(task_cli_runner_env):
    """Test basic task showing using project and task slugs."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create a task first
    task_name = "Show Task 1"
    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                        '--project', project_slug, '--name', task_name])
    assert result_create.exit_code == 0
    task_slug = json.loads(result_create.output)['data']['slug']
    task_id = json.loads(result_create.output)['data']['id']
    assert task_slug == "show-task-1"

    # Test task show using project slug and task slug
    result_show = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', project_slug, task_slug])
    assert result_show.exit_code == 0
    response_show = json.loads(result_show.output)
    assert response_show["status"] == "success"
    assert response_show["data"]["name"] == task_name
    assert response_show["data"]["slug"] == task_slug
    assert response_show["data"]["id"] == task_id


def test_task_show_not_found(task_cli_runner_env):
    """Test showing a non-existent task."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']
    non_existent_task_slug = "non-existent-show-task"

    result_show = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', project_slug, non_existent_task_slug])

    # Command should succeed but return error status
    assert result_show.exit_code == 0
    response_show = json.loads(result_show.output)
    assert response_show["status"] == "error"
    assert "Task not found" in response_show["message"]
    assert non_existent_task_slug in response_show["message"]


def test_task_show_wrong_project(task_cli_runner_env):
    """Test showing a task using the wrong project slug."""
    runner, db_path, project_info = task_cli_runner_env
    project_slug = project_info['project_slug']

    # Create a task
    task_name = "Wrong Project Show Task"
    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'task', 'create',
                                        '--project', project_slug, '--name', task_name])
    assert result_create.exit_code == 0
    task_slug = json.loads(result_create.output)['data']['slug']

    # Create another project
    other_project_name = "Other Project For Show"
    result_proj2 = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', other_project_name])
    assert result_proj2.exit_code == 0
    other_project_slug = json.loads(result_proj2.output)['data']['slug']

    # Try to show the task using the other project's slug
    result_show = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'task', 'show', other_project_slug, task_slug])

    # Command should succeed but return error status
    assert result_show.exit_code == 0
    response_show = json.loads(result_show.output)
    assert response_show["status"] == "error"
    # Task slug doesn't exist in other_project
    assert "Task not found" in response_show["message"]
    assert task_slug in response_show["message"]
    # Check for project name in message
    assert f"in project '{other_project_name}'" in response_show["message"]

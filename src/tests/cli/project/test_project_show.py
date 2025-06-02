import json
from pm.cli.__main__ import cli


def test_project_show(cli_runner_env):
    """Test 'project show' using both ID and slug."""
    runner, db_path = cli_runner_env

    # Setup: Create a project first
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Show Test Project'])
    assert result_create.exit_code == 0
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    project_id = response_create["data"]["id"]
    project_slug = response_create["data"]["slug"]
    assert project_slug == "show-test-project"

    # Test project show using ID
    result_show_id = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'show', project_id])
    assert result_show_id.exit_code == 0
    response_show_id = json.loads(result_show_id.output)
    assert response_show_id["status"] == "success"
    assert response_show_id["data"]["name"] == "Show Test Project"
    assert response_show_id["data"]["id"] == project_id
    assert response_show_id["data"]["slug"] == project_slug

    # Test project show using SLUG
    result_show_slug = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'show', project_slug])
    assert result_show_slug.exit_code == 0
    response_show_slug = json.loads(result_show_slug.output)
    assert response_show_slug["status"] == "success"
    # Verify correct project retrieved
    assert response_show_slug["data"]["id"] == project_id
    assert response_show_slug["data"]["name"] == "Show Test Project"
    assert response_show_slug["data"]["slug"] == project_slug


def test_project_show_not_found(cli_runner_env):
    """Test 'project show' for a non-existent project."""
    runner, db_path = cli_runner_env
    non_existent_id = "non-existent-id"
    non_existent_slug = "non-existent-slug"

    # Test show with non-existent ID
    result_show_id = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'show', non_existent_id])
    # Command succeeds, but returns error status
    assert result_show_id.exit_code == 0
    response_show_id = json.loads(result_show_id.output)
    assert response_show_id["status"] == "error"
    assert "Project not found" in response_show_id["message"]
    assert non_existent_id in response_show_id["message"]

    # Test show with non-existent slug
    result_show_slug = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'show', non_existent_slug])
    # Command succeeds, but returns error status
    assert result_show_slug.exit_code == 0
    response_show_slug = json.loads(result_show_slug.output)
    assert response_show_slug["status"] == "error"
    assert "Project not found" in response_show_slug["message"]
    assert non_existent_slug in response_show_slug["message"]

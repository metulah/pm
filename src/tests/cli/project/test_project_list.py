import json
from pm.cli.__main__ import cli


def test_project_list_empty(cli_runner_env):
    """Test listing projects when none exist."""
    runner, db_path = cli_runner_env
    result_list = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'list'])
    assert result_list.exit_code == 0
    response_list = json.loads(result_list.output)
    assert response_list["status"] == "success"
    assert len(response_list["data"]) == 0


def test_project_list_default_and_prospective_flag(cli_runner_env):
    """Test default listing (ACTIVE only) and listing with --prospective."""
    runner, db_path = cli_runner_env

    # Create one PROSPECTIVE project
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Prospective Proj 1'])
    assert result_create.exit_code == 0
    project_slug_1 = json.loads(result_create.output)["data"]["slug"]

    # Create one ACTIVE project
    result_create_active = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Active Proj 1', '--status', 'ACTIVE'])
    assert result_create_active.exit_code == 0
    active_slug = json.loads(result_create_active.output)['data']['slug']

    # Test default project listing (should only show ACTIVE)
    result_list_default = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'list'])
    assert result_list_default.exit_code == 0
    response_list_default = json.loads(result_list_default.output)
    assert response_list_default["status"] == "success"
    assert len(response_list_default["data"]) == 1
    assert response_list_default["data"][0]["slug"] == active_slug
    assert response_list_default["data"][0]["status"] == "ACTIVE"

    # Test listing WITH --prospective flag (should show ACTIVE and PROSPECTIVE)
    result_list_prospective = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'list', '--prospective'])
    assert result_list_prospective.exit_code == 0
    response_list_prospective = json.loads(result_list_prospective.output)
    assert response_list_prospective["status"] == "success"
    assert len(response_list_prospective["data"]) == 2
    listed_slugs = {p['slug'] for p in response_list_prospective["data"]}
    assert listed_slugs == {active_slug, project_slug_1}


def test_cli_project_list_all_flag(cli_runner_env):
    """Test 'project list --all' flag shows all statuses."""
    runner, db_path = cli_runner_env

    # Create projects with various statuses
    statuses_to_create = ["ACTIVE", "PROSPECTIVE",
                          "COMPLETED", "CANCELLED", "ARCHIVED"]
    project_slugs = {}
    for status in statuses_to_create:
        name = f"All Flag Test {status}"
        slug = f"all-flag-test-{status.lower()}"
        project_slugs[status] = slug
        result_create = runner.invoke(cli, ['--db-path', db_path, 'project', 'create',
                                            '--name', name, '--status', status])
        assert result_create.exit_code == 0, f"Failed to create {status} project"

    # 1. List without --all (should only show ACTIVE)
    result_list_default = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'list'])
    assert result_list_default.exit_code == 0
    response_default = json.loads(result_list_default.output)
    assert response_default['status'] == 'success'
    assert len(
        response_default['data']) == 1, "Default list should only contain ACTIVE project"
    assert response_default['data'][0]['slug'] == project_slugs["ACTIVE"]
    assert response_default['data'][0]['status'] == "ACTIVE"

    # 2. List with --all (should show all 5 projects)
    result_list_all = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'list', '--all'])
    assert result_list_all.exit_code == 0
    response_all = json.loads(result_list_all.output)
    assert response_all['status'] == 'success'
    assert len(response_all['data']) == len(
        statuses_to_create), "List with --all should show all projects"
    listed_slugs_all = {p['slug'] for p in response_all['data']}
    assert listed_slugs_all == set(project_slugs.values())

    # 3. List with --all and another status flag (e.g., --completed)
    #    --all should override the other flag, still showing all projects
    result_list_all_override = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'list', '--all', '--completed'])
    assert result_list_all_override.exit_code == 0
    response_all_override = json.loads(result_list_all_override.output)
    assert response_all_override['status'] == 'success'
    assert len(response_all_override['data']) == len(
        statuses_to_create), "--all should override other status flags"
    listed_slugs_override = {p['slug']
                             for p in response_all_override['data']}
    assert listed_slugs_override == set(project_slugs.values())

    # 4. List with just --completed (should show ACTIVE and COMPLETED)
    result_list_completed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'list', '--completed'])
    assert result_list_completed.exit_code == 0
    response_completed = json.loads(result_list_completed.output)
    assert response_completed['status'] == 'success'
    assert len(
        response_completed['data']) == 2, "List with --completed should show ACTIVE and COMPLETED"
    listed_slugs_completed = {p['slug']
                              for p in response_completed['data']}
    assert listed_slugs_completed == {
        project_slugs["ACTIVE"], project_slugs["COMPLETED"]}


def test_cli_project_list_text_format(cli_runner_env):
    """Test 'project list' text output format."""
    runner, db_path = cli_runner_env

    # Create ACTIVE and PROSPECTIVE projects
    result_create_active = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Active List Text', '--status', 'ACTIVE'])
    assert result_create_active.exit_code == 0
    active_slug = json.loads(result_create_active.output)['data']['slug']

    result_create_prospective = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Prospective List Text'])
    assert result_create_prospective.exit_code == 0
    prospective_slug = json.loads(result_create_prospective.output)[
        'data']['slug']

    # Default list (text format) should only show ACTIVE
    result_list_default = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list'])
    assert result_list_default.exit_code == 0
    assert active_slug in result_list_default.output
    assert " Active " in result_list_default.output  # Check for status text
    assert prospective_slug not in result_list_default.output
    assert " Prospective " not in result_list_default.output

    # List with --prospective flag (text format)
    result_list_prospective_flag = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list', '--prospective'])
    assert result_list_prospective_flag.exit_code == 0
    assert active_slug in result_list_prospective_flag.output
    assert " Active " in result_list_prospective_flag.output
    assert prospective_slug in result_list_prospective_flag.output
    assert " Prospective " in result_list_prospective_flag.output

import json
from pm.storage import init_db, get_project, list_projects
from pm.cli.__main__ import cli


def test_project_create_basic(cli_runner_env):
    """Test basic project creation with default status (PROSPECTIVE)."""
    runner, db_path = cli_runner_env

    # Verify database is empty initially
    with init_db(db_path) as conn:
        assert len(list_projects(conn)) == 0

    # Test project creation
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'CLI Project 1', '--description', 'Desc 1'])
    assert result_create.exit_code == 0, f"Output: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    assert response_create["data"]["name"] == "CLI Project 1"
    assert response_create["data"]["description"] == "Desc 1"
    assert response_create["data"]["status"] == "PROSPECTIVE", "Default status should be PROSPECTIVE"
    project_id_1 = response_create["data"]["id"]
    project_slug_1 = response_create["data"]["slug"]
    assert project_slug_1 == "cli-project-1"

    # Verify in DB
    with init_db(db_path) as conn:
        project = get_project(conn, project_id_1)
        assert project is not None
        assert project.name == "CLI Project 1"
        assert project.slug == "cli-project-1"
        assert project.status.value == "PROSPECTIVE"


def test_project_create_explicit_status(cli_runner_env):
    """Test creating a project with an explicit status."""
    runner, db_path = cli_runner_env

    # Explicitly create ACTIVE
    result_create_active = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Active Proj', '--status', 'ACTIVE'])
    assert result_create_active.exit_code == 0
    response_create_active = json.loads(result_create_active.output)
    assert response_create_active['status'] == 'success'
    assert response_create_active['data']['status'] == 'ACTIVE'
    active_slug = response_create_active['data']['slug']
    active_id = response_create_active['data']['id']

    # Verify in DB
    with init_db(db_path) as conn:
        project = get_project(conn, active_id)
        assert project is not None
        assert project.name == "Active Proj"
        assert project.slug == active_slug
        assert project.status.value == "ACTIVE"


def test_project_create_description_from_file(cli_runner_env, tmp_path):
    """Test 'project create --description @filepath' reads description from file."""
    runner, db_path = cli_runner_env

    desc_content = "Description for project create from file."
    filepath = tmp_path / "proj_desc_create.txt"
    filepath.write_text(desc_content, encoding='utf-8')

    # Attempt to create using @filepath for description
    result_create = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'create',
                                  '--name', 'Create Desc File Test',
                                        '--description', f"@{filepath}"])

    assert result_create.exit_code == 0, f"CLI Error: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"

    # Verify the description matches the file content, not the literal '@filepath'
    assert response_create["data"]["description"] == desc_content, "Description should match file content"
    assert response_create["data"]["description"] != f"@{filepath}", "Description should not be the literal filepath string"

    # Verify in DB as well
    project_id = response_create["data"]["id"]
    conn = init_db(db_path)
    project = get_project(conn, project_id)
    conn.close()
    assert project is not None
    assert project.description == desc_content


def test_project_create_status_case_insensitive(cli_runner_env):
    """Test creating projects with case-insensitive status values."""
    runner, db_path = cli_runner_env

    # 1. Test lowercase status: active
    result_create_lower = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Case Test Proj Lower', '--status', 'active'])
    assert result_create_lower.exit_code == 0, f"Create with lowercase status failed: {result_create_lower.output}"
    response_lower = json.loads(result_create_lower.output)
    assert response_lower['status'] == 'success'
    assert response_lower['data']['status'] == 'ACTIVE', "Status should be stored as uppercase ACTIVE"
    lower_id = response_lower['data']['id']

    # Verify in DB
    with init_db(db_path) as conn:
        project_lower = get_project(conn, lower_id)
        assert project_lower is not None
        assert project_lower.status.value == "ACTIVE"

    # 2. Test mixed-case status: COMPleted
    result_create_mixed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Case Test Proj Mixed', '--status', 'COMPleted'])
    assert result_create_mixed.exit_code == 0, f"Create with mixed-case status failed: {result_create_mixed.output}"
    response_mixed = json.loads(result_create_mixed.output)
    assert response_mixed['status'] == 'success'
    assert response_mixed['data']['status'] == 'COMPLETED', "Status should be stored as uppercase COMPLETED"
    mixed_id = response_mixed['data']['id']

    # Verify in DB
    with init_db(db_path) as conn:
        project_mixed = get_project(conn, mixed_id)
        assert project_mixed is not None
        assert project_mixed.status.value == "COMPLETED"

    # 3. Test invalid status value (should fail regardless of case)
    result_create_invalid = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Case Test Proj Invalid', '--status', 'invalidStatus'])
    assert result_create_invalid.exit_code != 0, "Create with invalid status should fail"
    # Click's error message for invalid choice
    assert "Invalid value for '--status'" in result_create_invalid.output or "Invalid value for '--status'" in result_create_invalid.stderr

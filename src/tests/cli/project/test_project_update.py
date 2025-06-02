import json
from pm.storage import init_db, get_project
from pm.cli.__main__ import cli


def test_project_update_basic(cli_runner_env):
    """Test basic project update for name and description using slug."""
    runner, db_path = cli_runner_env

    # Setup: Create a project first
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Update Test Project', '--description', 'Initial Desc'])
    assert result_create.exit_code == 0
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    project_id = response_create["data"]["id"]
    project_slug = response_create["data"]["slug"]
    assert project_slug == "update-test-project"

    # Test project update using SLUG
    result_update = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                  project_slug, '--name', 'Updated Project Name', '--description', 'New Desc'])
    assert result_update.exit_code == 0
    response_update = json.loads(result_update.output)
    assert response_update["status"] == "success"
    assert response_update["data"]["name"] == "Updated Project Name"
    assert response_update["data"]["description"] == "New Desc"
    # Slug should be immutable
    assert response_update["data"]["slug"] == project_slug
    # Ensure ID hasn't changed
    assert response_update["data"]["id"] == project_id

    # Verify in DB
    conn = init_db(db_path)
    project = get_project(conn, project_id)
    conn.close()
    assert project is not None
    assert project.name == "Updated Project Name"
    assert project.description == "New Desc"
    assert project.slug == project_slug


def test_cli_project_status_updates(cli_runner_env):
    """Test updating project status through valid and invalid transitions using slugs."""
    runner, db_path = cli_runner_env

    # 1. Create Project (Default status should be PROSPECTIVE)
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Status Update Test Proj 1'])
    assert result_create.exit_code == 0, f"Create failed: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create['status'] == 'success'
    assert response_create['data']['status'] == 'PROSPECTIVE', "Default status should be PROSPECTIVE"
    project_slug_1 = response_create['data']['slug']

    # 2. Test valid transition: PROSPECTIVE -> ACTIVE
    result_update_active = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'update', project_slug_1, '--status', 'ACTIVE'])
    assert result_update_active.exit_code == 0, f"Update PROSPECTIVE->ACTIVE failed: {result_update_active.output}"
    assert "Reminder: Project status updated." in result_update_active.stderr
    response_update_active = json.loads(result_update_active.output)
    assert response_update_active['status'] == 'success'
    assert response_update_active['data']['status'] == 'ACTIVE'

    # 3. Test valid transition: ACTIVE -> CANCELLED
    result_update_cancelled = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'update', project_slug_1, '--status', 'CANCELLED'])
    assert result_update_cancelled.exit_code == 0, f"Update ACTIVE->CANCELLED failed: {result_update_cancelled.output}"
    assert "Reminder: Project status updated." in result_update_cancelled.stderr
    response_update_cancelled = json.loads(result_update_cancelled.output)
    assert response_update_cancelled['status'] == 'success'
    assert response_update_cancelled['data']['status'] == 'CANCELLED'

    # 4. Test valid transition: CANCELLED -> ARCHIVED
    result_update_archived = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'update', project_slug_1, '--status', 'ARCHIVED'])
    assert result_update_archived.exit_code == 0, f"Update CANCELLED->ARCHIVED failed: {result_update_archived.output}"
    assert "Reminder: Project status updated." in result_update_archived.stderr
    response_update_archived = json.loads(result_update_archived.output)
    assert response_update_archived['status'] == 'success'
    assert response_update_archived['data']['status'] == 'ARCHIVED'

    # 5. Create another project (default PROSPECTIVE)
    result_create_2 = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Status Update Test Proj 2'])
    assert result_create_2.exit_code == 0
    response_create_2 = json.loads(result_create_2.output)
    assert response_create_2['data']['status'] == 'PROSPECTIVE'
    project_slug_2 = response_create_2['data']['slug']

    # 6. Test valid transition: PROSPECTIVE -> CANCELLED
    result_update_p_cancelled = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'update', project_slug_2, '--status', 'CANCELLED'])
    assert result_update_p_cancelled.exit_code == 0, f"Update PROSPECTIVE->CANCELLED failed: {result_update_p_cancelled.output}"
    assert "Reminder: Project status updated." in result_update_p_cancelled.stderr
    response_update_p_cancelled = json.loads(result_update_p_cancelled.output)
    assert response_update_p_cancelled['status'] == 'success'
    assert response_update_p_cancelled['data']['status'] == 'CANCELLED'

    # 7. Test INVALID transition: ACTIVE -> PROSPECTIVE
    #    (Need an ACTIVE project first)
    result_create_active = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Active Proj For Invalid Update', '--status', 'ACTIVE'])
    assert result_create_active.exit_code == 0
    active_slug = json.loads(result_create_active.output)['data']['slug']

    result_update_invalid = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'update', active_slug, '--status', 'PROSPECTIVE'])
    # Expect failure (non-zero exit code)
    assert result_update_invalid.exit_code != 0, "Update ACTIVE->PROSPECTIVE should fail"
    # Expect specific error message in stderr
    assert "Invalid project status transition: ACTIVE -> PROSPECTIVE" in result_update_invalid.stderr


def test_project_update_description_from_file_success(cli_runner_env, tmp_path):
    """Test 'project update --description @filepath' successfully reads file."""
    runner, db_path = cli_runner_env
    # Setup: Create a project
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Desc File Update Test Proj'])
    assert result_create.exit_code == 0
    project_data = json.loads(result_create.output)['data']
    project_slug = project_data['slug']
    project_id = project_data['id']

    desc_content = "Description for project update from file."
    filepath = tmp_path / "proj_desc_update.txt"
    filepath.write_text(desc_content, encoding='utf-8')

    # Attempt to update using @filepath
    result_update = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                  project_slug, '--description', f"@{filepath}"])

    assert result_update.exit_code == 0, f"CLI Error: {result_update.output}"
    response_update = json.loads(result_update.output)
    assert response_update["status"] == "success"

    # Check that the description WAS correctly read from the file.
    assert response_update["data"]["description"] == desc_content
    # Ensure it's not the literal string
    assert response_update["data"]["description"] != f"@{filepath}"

    # Verify in DB as well
    conn = init_db(db_path)
    project = get_project(conn, project_id)
    conn.close()
    assert project is not None
    assert project.description == desc_content
    assert project.description != f"@{filepath}"


def test_project_update_not_found(cli_runner_env):
    """Test 'project update' for a non-existent project."""
    runner, db_path = cli_runner_env
    non_existent_slug = "non-existent-update-slug"

    result_update = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                  non_existent_slug, '--name', 'Wont Happen'])

    assert result_update.exit_code == 0  # Command succeeds, but returns error status
    response_update = json.loads(result_update.output)
    assert response_update["status"] == "error"
    assert "Project not found" in response_update["message"]
    assert non_existent_slug in response_update["message"]


def test_project_update_status_case_insensitive(cli_runner_env):
    """Test updating project status with case-insensitive values."""
    runner, db_path = cli_runner_env

    # 1. Create Project (Default status PROSPECTIVE)
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Case Test Proj'])
    assert result_create.exit_code == 0, f"Create failed: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create['status'] == 'success'
    project_slug = response_create['data']['slug']
    assert response_create['data']['status'] == 'PROSPECTIVE'

    # 2. Test lowercase status: prospective -> active
    result_update_lower = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'update', project_slug, '--status', 'active'])
    assert result_update_lower.exit_code == 0, f"Update prospective->active (lowercase) failed: {result_update_lower.output}"
    response_update_lower = json.loads(result_update_lower.output)
    assert response_update_lower['status'] == 'success'
    assert response_update_lower['data']['status'] == 'ACTIVE', "Status should be stored as uppercase ACTIVE"
    assert "Reminder: Project status updated." in result_update_lower.stderr

    # 3. Test mixed-case status: ACTIVE -> Completed
    result_update_mixed = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'update', project_slug, '--status', 'Completed'])
    assert result_update_mixed.exit_code == 0, f"Update ACTIVE->Completed (mixed-case) failed: {result_update_mixed.output}"
    response_update_mixed = json.loads(result_update_mixed.output)
    assert response_update_mixed['status'] == 'success'
    assert response_update_mixed['data']['status'] == 'COMPLETED', "Status should be stored as uppercase COMPLETED"
    assert "Reminder: Project status updated." in result_update_mixed.stderr

    # 4. Test uppercase status (as baseline): COMPLETED -> ARCHIVED
    result_update_upper = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'update', project_slug, '--status', 'ARCHIVED'])
    assert result_update_upper.exit_code == 0, f"Update COMPLETED->ARCHIVED (uppercase) failed: {result_update_upper.output}"
    response_update_upper = json.loads(result_update_upper.output)
    assert response_update_upper['status'] == 'success'
    assert response_update_upper['data']['status'] == 'ARCHIVED', "Status should be stored as uppercase ARCHIVED"
    assert "Reminder: Project status updated." in result_update_upper.stderr

    # 5. Test invalid status value (should fail regardless of case)
    result_update_invalid = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'update', project_slug, '--status', 'invalidStatus'])
    assert result_update_invalid.exit_code != 0, "Update with invalid status should fail"
    # Click's error message for invalid choice
    assert "Invalid value for '--status'" in result_update_invalid.output or "Invalid value for '--status'" in result_update_invalid.stderr

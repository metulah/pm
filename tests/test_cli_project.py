"""Tests for project CLI commands."""

import pytest
import json
import os
from pathlib import Path
from pm.storage import init_db, get_project, get_project_by_slug  # Add import
from pm.cli.__main__ import cli  # Import the main cli entry point
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

# --- CLI Tests ---


def test_cli_project_crud(cli_runner_env):
    """Test basic project create, list, show, update via CLI using slugs."""
    runner, db_path = cli_runner_env
    from pm.storage import list_projects  # For verification

    # Verify database is empty initially
    with init_db(db_path) as conn:
        assert len(list_projects(conn)) == 0

    # Test project creation (JSON default)
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'CLI Project 1', '--description', 'Desc 1'])
    assert result_create.exit_code == 0, f"Output: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    assert response_create["data"]["name"] == "CLI Project 1"
    # Default is now PROSPECTIVE
    assert response_create["data"]["status"] == "PROSPECTIVE"
    project_id_1 = response_create["data"]["id"]
    project_slug_1 = response_create["data"]["slug"]  # Get slug
    assert project_slug_1 == "cli-project-1"  # Verify expected slug

    # Test project listing (JSON default)
    result_list = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'list'])
    assert result_list.exit_code == 0
    response_list = json.loads(result_list.output)
    assert response_list["status"] == "success"
    assert len(response_list["data"]) == 1
    assert response_list["data"][0]["id"] == project_id_1
    # Verify slug in list
    assert response_list["data"][0]["slug"] == project_slug_1

    # Test project show using ID
    result_show_id = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'show', project_id_1])
    assert result_show_id.exit_code == 0
    response_show_id = json.loads(result_show_id.output)
    assert response_show_id["status"] == "success"
    assert response_show_id["data"]["name"] == "CLI Project 1"
    # Verify slug in show
    assert response_show_id["data"]["slug"] == project_slug_1

    # Test project show using SLUG
    result_show_slug = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'show', project_slug_1])
    assert result_show_slug.exit_code == 0
    response_show_slug = json.loads(result_show_slug.output)
    assert response_show_slug["status"] == "success"
    # Verify correct project retrieved
    assert response_show_slug["data"]["id"] == project_id_1
    assert response_show_slug["data"]["slug"] == project_slug_1

    # Test project update using SLUG
    result_update = runner.invoke(cli, ['--db-path', db_path, '--format', 'json', 'project', 'update',
                                  project_slug_1, '--name', 'Updated Project 1', '--description', 'New Desc'])
    assert result_update.exit_code == 0
    response_update = json.loads(result_update.output)
    assert response_update["status"] == "success"
    assert response_update["data"]["name"] == "Updated Project 1"
    assert response_update["data"]["description"] == "New Desc"
    # Slug should be immutable
    assert response_update["data"]["slug"] == project_slug_1


def test_cli_project_status(cli_runner_env):
    """Test creating (default PROSPECTIVE) and updating project status using slugs."""
    runner, db_path = cli_runner_env

    # 1. Create Project (Default status should be PROSPECTIVE)
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Status Test Proj 1'])
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
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Status Test Proj 2'])
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
        # Explicitly create ACTIVE
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Active Proj', '--status', 'ACTIVE'])
    assert result_create_active.exit_code == 0
    active_slug = json.loads(result_create_active.output)['data']['slug']

    result_update_invalid = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'update', active_slug, '--status', 'PROSPECTIVE'])
    # Expect failure (non-zero exit code)
    assert result_update_invalid.exit_code != 0, "Update ACTIVE->PROSPECTIVE should fail"
    # Expect specific error message in stderr
    assert "Invalid project status transition: ACTIVE -> PROSPECTIVE" in result_update_invalid.stderr

    # 8. Verify listing shows PROSPECTIVE projects by default
    result_list = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list'])
    assert result_list.exit_code == 0
    # Project 1 is ARCHIVED, Project 2 is CANCELLED, Active Proj is ACTIVE
    # We need one more PROSPECTIVE project to check listing
    result_create_3 = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Status Test Proj 3'])
    assert result_create_3.exit_code == 0
    project_slug_3 = json.loads(result_create_3.output)['data']['slug']
    assert json.loads(result_create_3.output)[
        'data']['status'] == 'PROSPECTIVE'

    result_list_final = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list'])
    assert result_list_final.exit_code == 0
    # Check the new prospective one is listed
    assert project_slug_3 in result_list_final.output
    # Check the status column header/value exists
    assert "PROSPECTIVE" in result_list_final.output
    # Active should also be listed by default
    assert active_slug in result_list_final.output
    assert "ACTIVE" in result_list_final.output
    # Archived should NOT be listed by default
    assert project_slug_1 not in result_list_final.output
    # Cancelled should NOT be listed by default
    assert project_slug_2 not in result_list_final.output
# Rename test


def test_project_update_description_from_file_success(cli_runner_env, tmp_path):
    """Test 'project update --description @filepath' successfully reads file."""
    runner, db_path = cli_runner_env
    # Setup: Create a project
    result_create = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'json', 'project', 'create', '--name', 'Desc File Test Proj'])
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

    # *** This assertion should now PASS ***
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

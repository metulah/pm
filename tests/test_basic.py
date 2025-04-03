import pytest
import sqlite3
import json
from pm.models import Project, Task
from pm.storage import init_db


@pytest.fixture
def db_connection(tmp_path):
    """Fixture providing a clean database connection for each test."""
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)
    yield conn
    conn.close()


def test_project_creation(db_connection):
    """Test creating and retrieving a project."""
    project = Project(
        id="test-project",
        name="Test Project",
        description="A test project"
    )

    # Test create_project
    from pm.storage import create_project
    created_project = create_project(db_connection, project)
    assert created_project.id == "test-project"
    assert created_project.name == "Test Project"

    # Test get_project
    from pm.storage import get_project
    retrieved_project = get_project(db_connection, "test-project")
    assert retrieved_project.id == "test-project"
    assert retrieved_project.name == "Test Project"


def test_task_creation(db_connection):
    """Test creating and retrieving a task."""
    # First create a project
    from pm.storage import create_project
    project = create_project(db_connection, Project(
        id="test-project",
        name="Test Project"
    ))

    # Test create_task
    from pm.storage import create_task
    task = Task(
        id="test-task",
        project_id="test-project",
        name="Test Task"
    )
    created_task = create_task(db_connection, task)
    assert created_task.id == "test-task"
    assert created_task.project_id == "test-project"

    # Test get_task
    from pm.storage import get_task
    retrieved_task = get_task(db_connection, "test-task")
    assert retrieved_task.id == "test-task"
    assert retrieved_task.project_id == "test-project"


def test_cli_commands(tmp_path):  # Remove monkeypatch fixture
    """Test basic CLI commands using --db-path option."""
    from pm.cli import cli
    from click.testing import CliRunner
    # Import needed storage functions
    from pm.storage import init_db, list_projects, get_project, get_task

    # Use a fresh temporary database
    db_path = str(tmp_path / "test.db")  # Use string path
    conn = init_db(db_path)  # Initialize the db file
    conn.close()  # Close initial connection

    # No more monkeypatching needed here

    runner = CliRunner()

    # Verify database is empty
    with init_db(db_path) as conn:
        assert len(list_projects(conn)) == 0

    # Test project creation via CLI
    # Pass --db-path *before* the command group
    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'CLI Project', '--description', 'CLI Test'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert response["data"]["name"] == "CLI Project"
    cli_project_id = response["data"]["id"]  # Store ID for later use

    # Test project listing via CLI
    # Pass --db-path *before* the command group
    # Test project listing (JSON default)
    result_list_json = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'list'])
    assert result_list_json.exit_code == 0
    response_list_json = json.loads(result_list_json.output)
    assert response_list_json["status"] == "success"
    projects_json = response_list_json["data"]
    assert len(projects_json) >= 1
    assert any(p["name"] == "CLI Project" for p in projects_json)
    # Use the ID we stored earlier
    project_id = cli_project_id

    # Test project listing (Text format)
    result_list_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list'])
    assert result_list_text.exit_code == 0
    # Check for table headers and project name in text output
    assert "ID" in result_list_text.output
    assert "NAME" in result_list_text.output
    assert "DESCRIPTION" in result_list_text.output
    assert "CLI Project" in result_list_text.output
    assert project_id in result_list_text.output  # Check if ID is present

    # Test project show (Text format)
    result_show_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'show', project_id])
    assert result_show_text.exit_code == 0
    assert f"Id:          {project_id}" in result_show_text.output
    assert "Name:        CLI Project" in result_show_text.output
    assert "Description: CLI Test" in result_show_text.output

    # Test task creation via CLI
    result = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_id, '--name', 'CLI Task'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert response["data"]["name"] == "CLI Task"
    task_id = response["data"]["id"]  # Get the created task ID for CLI Project

    # Test deleting project with task (should fail)
    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_id])
    assert result.exit_code == 0  # Command handles error gracefully
    response = json.loads(result.output)
    assert response["status"] == "error"
    assert "Cannot delete project" in response["message"]
    assert "contains 1 task(s)" in response["message"]

    # Test deleting the task
    result = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'delete', task_id])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"

    # Test deleting project without task (should succeed)
    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_id])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert "deleted" in response["message"]

    # Verify project is gone
    result = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'show', project_id])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "error"
    assert "not found" in response["message"]

    # --- Test Task Moving ---
    # Create Project A and Project B
    result_a = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Project A'])
    project_a_id = json.loads(result_a.output)['data']['id']
    result_b = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Project B'])
    project_b_id = json.loads(result_b.output)['data']['id']

    # Create Task 1 in Project A
    result_task = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_a_id, '--name', 'Task 1'])
    task_1_id = json.loads(result_task.output)[
        'data']['id']  # Task in Project A

    # Verify Task 1 is in Project A
    result_show = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'show', task_1_id])
    assert json.loads(result_show.output)['data']['project_id'] == project_a_id

    # Attempt to move Task 1 to non-existent project (should fail)
    result_move_fail = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'update', task_1_id, '--project', 'non-existent-project'])
    assert result_move_fail.exit_code == 0  # CLI handles error
    response_fail = json.loads(result_move_fail.output)
    assert response_fail['status'] == 'error'
    assert "Target project 'non-existent-project' not found" in response_fail['message']

    # Move Task 1 to Project B (should succeed)
    result_move_ok = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'update', task_1_id, '--project', project_b_id])
    assert result_move_ok.exit_code == 0
    response_ok = json.loads(result_move_ok.output)
    assert response_ok['status'] == 'success'
    assert response_ok['data']['project_id'] == project_b_id

    # Verify Task 1 is now in Project B
    result_show_after = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'show', task_1_id])
    assert json.loads(result_show_after.output)[
        'data']['project_id'] == project_b_id

    # Test task list (Text format) - should show Task 1 in Project B
    result_task_list_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', project_b_id])
    assert result_task_list_text.exit_code == 0
    assert "ID" in result_task_list_text.output
    assert "NAME" in result_task_list_text.output
    assert "STATUS" in result_task_list_text.output
    assert "Task 1" in result_task_list_text.output
    assert task_1_id in result_task_list_text.output

    # Test task show (Text format)
    result_task_show_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'show', task_1_id])
    assert result_task_show_text.exit_code == 0
    assert f"Id:          {task_1_id}" in result_task_show_text.output
    # Verify it's in Project B
    assert f"Project Id:  {project_b_id}" in result_task_show_text.output
    assert "Name:        Task 1" in result_task_show_text.output

    # --- Test Force Project Deletion ---
    # Create Project C with Task 2 and Task 3
    result_c = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Project C'])
    project_c_id = json.loads(result_c.output)['data']['id']
    result_task2 = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_c_id, '--name', 'Task 2'])
    task_2_id = json.loads(result_task2.output)['data']['id']
    result_task3 = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_c_id, '--name', 'Task 3'])
    task_3_id = json.loads(result_task3.output)['data']['id']

    # Attempt delete without force (should fail)
    result_del_noforce = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_c_id])
    assert result_del_noforce.exit_code == 0  # CLI handles error
    response_del_noforce = json.loads(result_del_noforce.output)
    assert response_del_noforce['status'] == 'error'
    assert "Cannot delete project" in response_del_noforce['message']
    assert "contains 2 task(s)" in response_del_noforce['message']

    # Attempt delete with force (should succeed)
    result_del_force = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_c_id, '--force'])
    assert result_del_force.exit_code == 0
    response_del_force = json.loads(result_del_force.output)
    assert response_del_force['status'] == 'success'
    assert "deleted" in response_del_force['message']

    # Verify Project C is gone
    result_show_c = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'show', project_c_id])
    assert json.loads(result_show_c.output)['status'] == 'error'
    assert "not found" in json.loads(result_show_c.output)['message']

    # Verify Task 2 is gone
    result_show_t2 = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'show', task_2_id])
    assert json.loads(result_show_t2.output)['status'] == 'error'
    assert "not found" in json.loads(result_show_t2.output)['message']

    # Verify Task 3 is gone
    result_show_t3 = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'show', task_3_id])
    assert json.loads(result_show_t3.output)['status'] == 'error'
    assert "not found" in json.loads(result_show_t3.output)['message']

    # Test simple message output (Text format) - e.g., delete success
    # Re-create Project A for deletion test
    result_a_del = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Project A Delete'])
    project_a_del_id = json.loads(result_a_del.output)['data']['id']
    result_del_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'delete', project_a_del_id])
    assert result_del_text.exit_code == 0
    assert f"Success: Project {project_a_del_id} deleted" in result_del_text.output

    # Test simple message output (Text format) - e.g., error
    result_del_err_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'delete', 'non-existent-project-id'])
    assert result_del_err_text.exit_code == 0
    assert "Error: Project non-existent-project-id not found" in result_del_err_text.output

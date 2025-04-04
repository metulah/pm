import pytest
import sqlite3
import json
from pm.models import Project, Task
from pm.storage import init_db
from pm.cli import cli  # Import the main cli entry point
from click.testing import CliRunner


@pytest.fixture
def db_connection(tmp_path):
    """Fixture providing a clean database connection for each test."""
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)
    yield conn
    conn.close()

# --- Fixture for CLI Runner and DB Path ---


@pytest.fixture
def cli_runner_env(tmp_path):
    """Fixture providing a CliRunner and a temporary db_path."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)  # Initialize the db file
    conn.close()  # Close initial connection
    runner = CliRunner(mix_stderr=False)  # Don't mix stdout/stderr
    return runner, db_path

# --- Storage Layer Tests (Keep existing ones) ---


def test_project_creation_storage(db_connection):
    """Test creating and retrieving a project via storage functions."""
    project = Project(
        id="test-project-storage",
        name="Test Project Storage",
        description="A test project via storage"
    )
    from pm.storage import create_project, get_project
    created_project = create_project(db_connection, project)
    assert created_project.id == "test-project-storage"
    assert created_project.name == "Test Project Storage"

    retrieved_project = get_project(db_connection, "test-project-storage")
    assert retrieved_project.id == "test-project-storage"
    assert retrieved_project.name == "Test Project Storage"
    assert retrieved_project.status.value == "ACTIVE"  # Check default status


def test_task_creation_storage(db_connection):
    """Test creating and retrieving a task via storage functions."""
    from pm.storage import create_project, create_task, get_task
    project = create_project(db_connection, Project(
        id="test-project-for-task",
        name="Test Project for Task"
    ))
    task = Task(
        id="test-task-storage",
        project_id="test-project-for-task",
        name="Test Task Storage"
    )
    created_task = create_task(db_connection, task)
    assert created_task.id == "test-task-storage"
    assert created_task.project_id == "test-project-for-task"

    retrieved_task = get_task(db_connection, "test-task-storage")
    assert retrieved_task.id == "test-task-storage"
    assert retrieved_task.project_id == "test-project-for-task"

# --- CLI Layer Tests (Refactored) ---


def test_cli_project_crud(cli_runner_env):
    """Test basic project create, list, show, update via CLI."""
    runner, db_path = cli_runner_env
    from pm.storage import list_projects  # For verification

    # Verify database is empty initially
    with init_db(db_path) as conn:
        assert len(list_projects(conn)) == 0

    # Test project creation (JSON default)
    result_create = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'CLI Project 1', '--description', 'Desc 1'])
    # Add output on failure
    assert result_create.exit_code == 0, f"Output: {result_create.output}"
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    assert response_create["data"]["name"] == "CLI Project 1"
    assert response_create["data"]["status"] == "ACTIVE"
    project_id_1 = response_create["data"]["id"]

    # Test project listing (JSON default)
    result_list = runner.invoke(cli, ['--db-path', db_path, 'project', 'list'])
    assert result_list.exit_code == 0
    response_list = json.loads(result_list.output)
    assert response_list["status"] == "success"
    assert len(response_list["data"]) == 1
    assert response_list["data"][0]["id"] == project_id_1

    # Test project show (JSON default)
    result_show = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'show', project_id_1])
    assert result_show.exit_code == 0
    response_show = json.loads(result_show.output)
    assert response_show["status"] == "success"
    assert response_show["data"]["name"] == "CLI Project 1"

    # Test project update (JSON default)
    result_update = runner.invoke(cli, ['--db-path', db_path, 'project', 'update',
                                  project_id_1, '--name', 'Updated Project 1', '--description', 'New Desc'])
    assert result_update.exit_code == 0
    response_update = json.loads(result_update.output)
    assert response_update["status"] == "success"
    assert response_update["data"]["name"] == "Updated Project 1"
    assert response_update["data"]["description"] == "New Desc"


def test_cli_task_crud(cli_runner_env):
    """Test basic task create, list, show, update via CLI."""
    runner, db_path = cli_runner_env

    # Setup: Create a project first
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Task Test Project'])
    project_id = json.loads(result_proj.output)['data']['id']

    # Test task creation
    result_create = runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                                  '--project', project_id, '--name', 'CLI Task 1', '--description', 'Task Desc 1'])
    assert result_create.exit_code == 0
    response_create = json.loads(result_create.output)
    assert response_create["status"] == "success"
    assert response_create["data"]["name"] == "CLI Task 1"
    task_id_1 = response_create["data"]["id"]

    # Test task listing
    result_list = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'list', '--project', project_id])
    assert result_list.exit_code == 0
    response_list = json.loads(result_list.output)
    assert response_list["status"] == "success"
    assert len(response_list["data"]) == 1
    assert response_list["data"][0]["id"] == task_id_1

    # Test task show
    result_show = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'show', task_id_1])
    assert result_show.exit_code == 0
    response_show = json.loads(result_show.output)
    assert response_show["status"] == "success"
    assert response_show["data"]["name"] == "CLI Task 1"

    # Test task update
    result_update = runner.invoke(cli, ['--db-path', db_path, 'task', 'update',
                                  task_id_1, '--name', 'Updated Task 1', '--status', 'IN_PROGRESS'])
    assert result_update.exit_code == 0
    response_update = json.loads(result_update.output)
    assert response_update["status"] == "success"
    assert response_update["data"]["name"] == "Updated Task 1"
    assert response_update["data"]["status"] == "IN_PROGRESS"


def test_cli_project_delete_standard(cli_runner_env):
    """Test standard project deletion logic (fail with task, success empty)."""
    runner, db_path = cli_runner_env

    # Setup: Create project and task
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Delete Test Project'])
    project_id = json.loads(result_proj.output)['data']['id']
    result_task = runner.invoke(cli, ['--db-path', db_path, 'task', 'create',
                                '--project', project_id, '--name', 'Task In Delete Project'])
    task_id = json.loads(result_task.output)['data']['id']

    # Test deleting project with task (should fail)
    result_del_fail = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_id])
    assert result_del_fail.exit_code == 0  # CLI handles error gracefully
    response_del_fail = json.loads(result_del_fail.output)
    assert response_del_fail["status"] == "error"
    assert "Cannot delete project" in response_del_fail["message"]
    assert "contains 1 task(s)" in response_del_fail["message"]

    # Test deleting the task
    result_del_task = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'delete', task_id])
    assert result_del_task.exit_code == 0
    assert json.loads(result_del_task.output)["status"] == "success"

    # Test deleting project without task (should succeed)
    result_del_ok = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'delete', project_id])
    assert result_del_ok.exit_code == 0
    response_del_ok = json.loads(result_del_ok.output)
    assert response_del_ok["status"] == "success"
    assert "deleted" in response_del_ok["message"]

    # Verify project is gone
    result_show = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'show', project_id])
    assert result_show.exit_code == 0
    assert json.loads(result_show.output)["status"] == "error"
    assert "not found" in json.loads(result_show.output)["message"]


def test_cli_task_move(cli_runner_env):
    """Test moving a task between projects."""
    runner, db_path = cli_runner_env

    # Setup: Create Project A and Project B
    result_a = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Project A'])
    project_a_id = json.loads(result_a.output)['data']['id']
    result_b = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Project B'])
    project_b_id = json.loads(result_b.output)['data']['id']

    # Create Task 1 in Project A
    result_task = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_a_id, '--name', 'Task 1'])
    task_1_id = json.loads(result_task.output)['data']['id']

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


def test_cli_project_delete_force(cli_runner_env):
    """Test force deleting a project with tasks."""
    runner, db_path = cli_runner_env

    # Setup: Create Project C with Task 2 and Task 3
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


def test_cli_output_format(cli_runner_env):
    """Test --format text vs json for list and show."""
    runner, db_path = cli_runner_env

    # Setup: Create a project and a task
    result_proj = runner.invoke(cli, ['--db-path', db_path, 'project', 'create',
                                '--name', 'Format Test Proj', '--description', 'Format Desc'])
    project_id = json.loads(result_proj.output)['data']['id']
    result_task = runner.invoke(
        cli, ['--db-path', db_path, 'task', 'create', '--project', project_id, '--name', 'Format Test Task'])
    task_id = json.loads(result_task.output)['data']['id']

    # Test project list (Text format)
    result_list_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list'])
    assert result_list_text.exit_code == 0
    assert "ID" in result_list_text.output
    assert "NAME" in result_list_text.output
    assert "STATUS" in result_list_text.output
    assert "Format Test Proj" in result_list_text.output
    assert project_id in result_list_text.output

    # Test project show (Text format)
    result_show_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'show', project_id])
    assert result_show_text.exit_code == 0
    assert f"Id:          {project_id}" in result_show_text.output
    assert "Name:        Format Test Proj" in result_show_text.output
    assert "Description: Format Desc" in result_show_text.output
    assert "Status:      ACTIVE" in result_show_text.output

    # Test task list (Text format)
    result_task_list_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'list', '--project', project_id])
    assert result_task_list_text.exit_code == 0
    assert "ID" in result_task_list_text.output
    assert "NAME" in result_task_list_text.output
    assert "STATUS" in result_task_list_text.output
    assert "Format Test Task" in result_task_list_text.output
    assert task_id in result_task_list_text.output

    # Test task show (Text format)
    result_task_show_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'task', 'show', task_id])
    assert result_task_show_text.exit_code == 0
    assert f"Id:          {task_id}" in result_task_show_text.output
    assert f"Project Id:  {project_id}" in result_task_show_text.output
    assert "Name:        Format Test Task" in result_task_show_text.output
    assert "Status:      NOT_STARTED" in result_task_show_text.output


def test_cli_project_status(cli_runner_env):
    """Test creating and updating project status."""
    runner, db_path = cli_runner_env

    # Create Project with COMPLETED status
    result_create = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Status Test Proj', '--status', 'COMPLETED'])
    assert result_create.exit_code == 0
    response_create = json.loads(result_create.output)
    assert response_create['status'] == 'success'
    assert response_create['data']['status'] == 'COMPLETED'
    project_id = response_create['data']['id']

    # Update status to ARCHIVED
    result_update = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'update', project_id, '--status', 'ARCHIVED'])
    assert result_update.exit_code == 0
    response_update = json.loads(result_update.output)
    assert response_update['status'] == 'success'
    assert response_update['data']['status'] == 'ARCHIVED'

    # Show (Text) and verify status
    result_show_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'show', project_id])
    assert result_show_text.exit_code == 0
    assert "Status:      ARCHIVED" in result_show_text.output

    # List (Text) and verify status
    result_list_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'list'])
    assert result_list_text.exit_code == 0
    assert "ARCHIVED" in result_list_text.output


def test_cli_simple_messages(cli_runner_env):
    """Test text format output for simple success/error messages."""
    runner, db_path = cli_runner_env

    # Setup: Create a project
    result_proj = runner.invoke(
        cli, ['--db-path', db_path, 'project', 'create', '--name', 'Message Test Proj'])
    project_id = json.loads(result_proj.output)['data']['id']

    # Test delete success message (Text format)
    result_del_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'delete', project_id])
    assert result_del_text.exit_code == 0
    assert f"Success: Project {project_id} deleted" in result_del_text.output

    # Test delete error message (Text format)
    result_del_err_text = runner.invoke(
        cli, ['--db-path', db_path, '--format', 'text', 'project', 'delete', 'non-existent-project-id'])
    assert result_del_err_text.exit_code == 0
    assert "Error: Project non-existent-project-id not found" in result_del_err_text.output

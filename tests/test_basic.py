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


def test_cli_commands(tmp_path):
    """Test basic CLI commands."""
    from pm.cli import cli
    from click.testing import CliRunner
    from pm.storage import init_db, list_projects

    # Use a fresh temporary database
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)
    conn.close()

    runner = CliRunner()

    # Verify database is empty
    with init_db(db_path) as conn:
        assert len(list_projects(conn)) == 0

    # Test project creation via CLI
    result = runner.invoke(
        cli, ['project', 'create', '--name', 'CLI Project', '--description', 'CLI Test'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert response["data"]["name"] == "CLI Project"

    # Test project listing via CLI
    result = runner.invoke(cli, ['project', 'list'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    projects = response["data"]
    assert len(projects) >= 1  # At least our new project should be there
    assert any(p["name"] == "CLI Project" for p in projects)
    assert response["data"][0]["name"] == "CLI Project"
    assert response["data"][0]["name"] == "CLI Project"

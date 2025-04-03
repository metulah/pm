import pytest
import sqlite3
import json
import datetime
from pm.models import Project, Task, TaskMetadata
from pm.storage import init_db, create_project, create_task, create_task_metadata, get_task_metadata
from pm.storage import update_task_metadata, delete_task_metadata, query_tasks_by_metadata


@pytest.fixture
def db_connection(tmp_path):
    """Fixture providing a clean database connection for each test."""
    db_path = tmp_path / "test.db"
    conn = init_db(db_path)
    yield conn
    conn.close()


@pytest.fixture
def test_task(db_connection):
    """Fixture providing a test task for metadata operations."""
    # Create a project
    project = create_project(db_connection, Project(
        id="test-project",
        name="Test Project"
    ))

    # Create a task
    task = create_task(db_connection, Task(
        id="test-task",
        project_id="test-project",
        name="Test Task"
    ))

    return task


def test_metadata_creation(db_connection, test_task):
    """Test creating and retrieving metadata."""
    # Create string metadata
    string_metadata = TaskMetadata.create(
        task_id=test_task.id,
        key="category",
        value="feature"
    )
    created_metadata = create_task_metadata(db_connection, string_metadata)
    assert created_metadata.task_id == test_task.id
    assert created_metadata.key == "category"
    assert created_metadata.value_type == "string"
    assert created_metadata.value_string == "feature"

    # Create int metadata
    int_metadata = TaskMetadata.create(
        task_id=test_task.id,
        key="priority",
        value=1,
        value_type="int"
    )
    created_metadata = create_task_metadata(db_connection, int_metadata)
    assert created_metadata.task_id == test_task.id
    assert created_metadata.key == "priority"
    assert created_metadata.value_type == "int"
    assert created_metadata.value_int == 1

    # Create datetime metadata
    now = datetime.datetime.now()
    datetime_metadata = TaskMetadata.create(
        task_id=test_task.id,
        key="due_date",
        value=now,
        value_type="datetime"
    )
    created_metadata = create_task_metadata(db_connection, datetime_metadata)
    assert created_metadata.task_id == test_task.id
    assert created_metadata.key == "due_date"
    assert created_metadata.value_type == "datetime"
    assert created_metadata.value_datetime == now

    # Retrieve all metadata
    metadata_list = get_task_metadata(db_connection, test_task.id)
    assert len(metadata_list) == 3

    # Retrieve specific metadata
    category_metadata = get_task_metadata(
        db_connection, test_task.id, "category")
    assert len(category_metadata) == 1
    assert category_metadata[0].key == "category"
    assert category_metadata[0].get_value() == "feature"


def test_metadata_update(db_connection, test_task):
    """Test updating metadata."""
    # Create initial metadata
    update_task_metadata(db_connection, test_task.id, "status", "pending")

    # Verify initial value
    metadata = get_task_metadata(db_connection, test_task.id, "status")
    assert metadata[0].get_value() == "pending"

    # Update the metadata
    update_task_metadata(db_connection, test_task.id, "status", "completed")

    # Verify updated value
    metadata = get_task_metadata(db_connection, test_task.id, "status")
    assert metadata[0].get_value() == "completed"


def test_metadata_delete(db_connection, test_task):
    """Test deleting metadata."""
    # Create metadata
    update_task_metadata(db_connection, test_task.id, "temporary", "value")

    # Verify it exists
    metadata = get_task_metadata(db_connection, test_task.id, "temporary")
    assert len(metadata) == 1

    # Delete the metadata
    result = delete_task_metadata(db_connection, test_task.id, "temporary")
    assert result is True

    # Verify it's gone
    metadata = get_task_metadata(db_connection, test_task.id, "temporary")
    assert len(metadata) == 0

    # Try deleting non-existent metadata
    result = delete_task_metadata(db_connection, test_task.id, "nonexistent")
    assert result is False


def test_metadata_query(db_connection):
    """Test querying tasks by metadata."""
    # Create two projects
    project1 = create_project(db_connection, Project(
        id="project1",
        name="Project 1"
    ))
    project2 = create_project(db_connection, Project(
        id="project2",
        name="Project 2"
    ))

    # Create tasks with different metadata
    task1 = create_task(db_connection, Task(
        id="task1",
        project_id="project1",
        name="Task 1"
    ))
    update_task_metadata(db_connection, task1.id, "priority", "high")

    task2 = create_task(db_connection, Task(
        id="task2",
        project_id="project1",
        name="Task 2"
    ))
    update_task_metadata(db_connection, task2.id, "priority", "medium")

    task3 = create_task(db_connection, Task(
        id="task3",
        project_id="project2",
        name="Task 3"
    ))
    update_task_metadata(db_connection, task3.id, "priority", "high")

    # Query tasks with high priority
    high_priority_tasks = query_tasks_by_metadata(
        db_connection, "priority", "high")
    assert len(high_priority_tasks) == 2
    assert any(t.id == "task1" for t in high_priority_tasks)
    assert any(t.id == "task3" for t in high_priority_tasks)

    # Query tasks with medium priority
    medium_priority_tasks = query_tasks_by_metadata(
        db_connection, "priority", "medium")
    assert len(medium_priority_tasks) == 1
    assert medium_priority_tasks[0].id == "task2"


def test_cli_metadata_commands(tmp_path, monkeypatch):
    """Test metadata CLI commands."""
    from pm.cli import cli, get_db_connection
    from click.testing import CliRunner
    import os

    # Use a fresh temporary database
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)

    # Create a project and task
    project = create_project(conn, Project(
        id="cli-project",
        name="CLI Project"
    ))

    task = create_task(conn, Task(
        id="cli-task",
        project_id="cli-project",
        name="CLI Task"
    ))

    conn.close()

    # Patch the get_db_connection function to use our test database
    def mock_get_db_connection():
        return init_db(db_path)

    monkeypatch.setattr('pm.cli.get_db_connection', mock_get_db_connection)

    runner = CliRunner()

    # Test setting metadata
    result = runner.invoke(
        cli, ['task', 'metadata', 'set', 'cli-task', '--key', 'status', '--value', 'in-progress'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert response["data"]["key"] == "status"
    assert response["data"]["value"] == "in-progress"

    # Test getting metadata
    result = runner.invoke(cli, ['task', 'metadata', 'get', 'cli-task'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert len(response["data"]) == 1
    assert response["data"][0]["key"] == "status"
    assert response["data"][0]["value"] == "in-progress"

    # Test getting specific metadata
    result = runner.invoke(
        cli, ['task', 'metadata', 'get', 'cli-task', '--key', 'status'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert len(response["data"]) == 1
    assert response["data"][0]["key"] == "status"

    # Test setting metadata with explicit type
    result = runner.invoke(
        cli, ['task', 'metadata', 'set', 'cli-task', '--key', 'priority', '--value', '1', '--type', 'int'])
    assert result.exit_code == 0

    # Test querying by metadata
    result = runner.invoke(
        cli, ['task', 'metadata', 'query', '--key', 'status', '--value', 'in-progress'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert len(response["data"]) == 1
    assert response["data"][0]["id"] == "cli-task"

    # Test deleting metadata
    result = runner.invoke(
        cli, ['task', 'metadata', 'delete', 'cli-task', '--key', 'status'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"

    # Verify metadata was deleted
    result = runner.invoke(
        cli, ['task', 'metadata', 'get', 'cli-task', '--key', 'status'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert len(response["data"]) == 0

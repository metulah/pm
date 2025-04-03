"""Test metadata functionality."""

import json
from pathlib import Path
from pm.models import Project, Task, TaskMetadata
from pm.storage import (
    init_db, create_project, create_task,
    create_task_metadata, get_task_metadata,
    get_task_metadata_value, update_task_metadata,
    delete_task_metadata, query_tasks_by_metadata
)


def test_create_metadata(tmp_path):
    """Test creating task metadata."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)

    # Create a project and task
    project = create_project(conn, Project(
        id="test-project",
        name="Test Project"
    ))

    task = create_task(conn, Task(
        id="test-task",
        project_id="test-project",
        name="Test Task"
    ))

    # Create metadata
    metadata = create_task_metadata(conn, TaskMetadata.create(
        task_id="test-task",
        key="priority",
        value=1
    ))

    assert metadata.task_id == "test-task"
    assert metadata.key == "priority"
    assert metadata.value_type == "int"
    assert metadata.value_int == 1

    conn.close()


def test_get_metadata(tmp_path):
    """Test getting task metadata."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)

    # Create a project and task
    project = create_project(conn, Project(
        id="test-project",
        name="Test Project"
    ))

    task = create_task(conn, Task(
        id="test-task",
        project_id="test-project",
        name="Test Task"
    ))

    # Create metadata
    create_task_metadata(conn, TaskMetadata.create(
        task_id="test-task",
        key="priority",
        value=1
    ))

    create_task_metadata(conn, TaskMetadata.create(
        task_id="test-task",
        key="status",
        value="in-progress"
    ))

    # Get all metadata
    metadata_list = get_task_metadata(conn, "test-task")
    assert len(metadata_list) == 2

    # Get specific metadata
    metadata_list = get_task_metadata(conn, "test-task", "priority")
    assert len(metadata_list) == 1
    assert metadata_list[0].key == "priority"
    assert metadata_list[0].value_int == 1

    # Get metadata value
    value = get_task_metadata_value(conn, "test-task", "status")
    assert value == "in-progress"

    conn.close()


def test_update_metadata(tmp_path):
    """Test updating task metadata."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)

    # Create a project and task
    project = create_project(conn, Project(
        id="test-project",
        name="Test Project"
    ))

    task = create_task(conn, Task(
        id="test-task",
        project_id="test-project",
        name="Test Task"
    ))

    # Create metadata
    create_task_metadata(conn, TaskMetadata.create(
        task_id="test-task",
        key="priority",
        value=1
    ))

    # Update metadata
    metadata = update_task_metadata(conn, "test-task", "priority", 2)
    assert metadata.value_int == 2

    # Verify update
    value = get_task_metadata_value(conn, "test-task", "priority")
    assert value == 2

    conn.close()


def test_delete_metadata(tmp_path):
    """Test deleting task metadata."""
    db_path = str(tmp_path / "test.db")
    conn = init_db(db_path)

    # Create a project and task
    project = create_project(conn, Project(
        id="test-project",
        name="Test Project"
    ))

    task = create_task(conn, Task(
        id="test-task",
        project_id="test-project",
        name="Test Task"
    ))

    # Create metadata
    create_task_metadata(conn, TaskMetadata.create(
        task_id="test-task",
        key="priority",
        value=1
    ))

    # Delete metadata
    success = delete_task_metadata(conn, "test-task", "priority")
    assert success

    # Verify deletion
    metadata_list = get_task_metadata(conn, "test-task")
    assert len(metadata_list) == 0

    conn.close()


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

    monkeypatch.setattr('pm.cli.base.get_db_connection',
                        mock_get_db_connection)

    runner = CliRunner()

    # Test setting metadata
    result = runner.invoke(
        cli, ['task', 'metadata', 'set', 'cli-task', '--key', 'status', '--value', 'in-progress'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert response["data"]["key"] == "status"
    assert response["data"]["value"] == "in-progress"

    # Test getting specific metadata
    result = runner.invoke(
        cli, ['task', 'metadata', 'get', 'cli-task', '--key', 'status'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert len(response["data"]) == 1
    assert response["data"][0]["key"] == "status"
    assert response["data"][0]["value"] == "in-progress"

    # Test setting metadata with explicit type
    result = runner.invoke(
        cli, ['task', 'metadata', 'set', 'cli-task', '--key', 'priority', '--value', '1', '--type', 'int'])
    assert result.exit_code == 0

    # Test getting all metadata
    result = runner.invoke(cli, ['task', 'metadata', 'get', 'cli-task'])
    assert result.exit_code == 0
    response = json.loads(result.output)
    assert response["status"] == "success"
    assert len(response["data"]) == 2  # Now we expect both status and priority

    # TODO: Test querying by metadata
    # result = runner.invoke(
    #     cli, ['task', 'metadata', 'query', '--key', 'status', '--value', 'in-progress'])
    # assert result.exit_code == 0
    # response = json.loads(result.output)
    # assert response["status"] == "success"
    # assert len(response["data"]) == 1

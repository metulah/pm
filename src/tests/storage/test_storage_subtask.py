import uuid
import pytest
from pm.models import Project, Task, Subtask, TaskStatus
from pm.storage import (
    init_db, create_project, create_task,
    create_subtask, get_subtask, update_subtask, delete_subtask, list_subtasks
)


@pytest.fixture
def db():
    """Create a test database connection."""
    conn = init_db(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def project(db):
    """Create a test project."""
    project = Project(
        id=str(uuid.uuid4()),
        name="Test Project",
        description="A test project"
    )
    return create_project(db, project)


@pytest.fixture
def task(db, project):
    """Create a test task."""
    task = Task(
        id=str(uuid.uuid4()),
        project_id=project.id,
        name="Test Task",
        description="A test task",
        status=TaskStatus.NOT_STARTED
    )
    return create_task(db, task)


def test_create_subtask(db, task):
    """Test creating a subtask."""
    subtask = Subtask(
        id=str(uuid.uuid4()),
        task_id=task.id,
        name="Test Subtask",
        description="A test subtask",
        required_for_completion=True,
        status=TaskStatus.NOT_STARTED
    )
    created_subtask = create_subtask(db, subtask)
    assert created_subtask.id == subtask.id
    assert created_subtask.task_id == task.id
    assert created_subtask.name == "Test Subtask"
    assert created_subtask.description == "A test subtask"
    assert created_subtask.required_for_completion is True
    assert created_subtask.status == TaskStatus.NOT_STARTED


def test_get_subtask(db, task):
    """Test retrieving a subtask by ID."""
    subtask = Subtask(
        id=str(uuid.uuid4()),
        task_id=task.id,
        name="Test Subtask",
        description="A test subtask",
        required_for_completion=True,
        status=TaskStatus.NOT_STARTED
    )
    create_subtask(db, subtask)

    retrieved_subtask = get_subtask(db, subtask.id)
    assert retrieved_subtask is not None
    assert retrieved_subtask.id == subtask.id
    assert retrieved_subtask.name == subtask.name
    assert retrieved_subtask.description == subtask.description
    assert retrieved_subtask.required_for_completion == subtask.required_for_completion
    assert retrieved_subtask.status == subtask.status


def test_update_subtask(db, task):
    """Test updating a subtask."""
    subtask = Subtask(
        id=str(uuid.uuid4()),
        task_id=task.id,
        name="Original Name",
        description="Original description",
        required_for_completion=True,
        status=TaskStatus.NOT_STARTED
    )
    create_subtask(db, subtask)

    updated_subtask = update_subtask(
        db, subtask.id,
        name="Updated Name",
        description="Updated description",
        required_for_completion=False,
        status=TaskStatus.IN_PROGRESS
    )
    assert updated_subtask is not None
    assert updated_subtask.name == "Updated Name"
    assert updated_subtask.description == "Updated description"
    assert updated_subtask.required_for_completion is False
    assert updated_subtask.status == TaskStatus.IN_PROGRESS


def test_delete_subtask(db, task):
    """Test deleting a subtask."""
    subtask = Subtask(
        id=str(uuid.uuid4()),
        task_id=task.id,
        name="Test Subtask",
        description="A test subtask",
        required_for_completion=True,
        status=TaskStatus.NOT_STARTED
    )
    create_subtask(db, subtask)

    success = delete_subtask(db, subtask.id)
    assert success is True

    deleted_subtask = get_subtask(db, subtask.id)
    assert deleted_subtask is None


def test_list_subtasks(db, task):
    """Test listing subtasks for a task."""
    subtasks = [
        Subtask(
            id=str(uuid.uuid4()),
            task_id=task.id,
            name=f"Subtask {i}",
            description=f"Description {i}",
            required_for_completion=True,
            status=TaskStatus.NOT_STARTED
        ) for i in range(3)
    ]

    for subtask in subtasks:
        create_subtask(db, subtask)

    task_subtasks = list_subtasks(db, task_id=task.id)
    assert len(task_subtasks) == 3
    assert all(s.task_id == task.id for s in task_subtasks)


def test_list_subtasks_by_status(db, task):
    """Test listing subtasks filtered by status."""
    # Create subtasks with different statuses
    statuses = [TaskStatus.NOT_STARTED,
                TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]
    for status in statuses:
        subtask = Subtask(
            id=str(uuid.uuid4()),
            task_id=task.id,
            name=f"Subtask {status.value}",
            description=f"Description for {status.value}",
            required_for_completion=True,
            status=status
        )
        create_subtask(db, subtask)

    # Test filtering by each status
    for status in statuses:
        filtered_subtasks = list_subtasks(db, task_id=task.id, status=status)
        assert len(filtered_subtasks) == 1
        assert all(s.status == status for s in filtered_subtasks)


def test_subtask_validation(db, task):
    """Test subtask validation."""
    # Test empty name
    with pytest.raises(ValueError, match="Subtask name cannot be empty"):
        Subtask(
            id=str(uuid.uuid4()),
            task_id=task.id,
            name="",
            description="Description"
        ).validate()

    # Test name too long
    with pytest.raises(ValueError, match="Subtask name cannot exceed 100 characters"):
        Subtask(
            id=str(uuid.uuid4()),
            task_id=task.id,
            name="x" * 101,
            description="Description"
        ).validate()

    # Test missing task_id
    with pytest.raises(ValueError, match="Subtask must be associated with a task"):
        Subtask(
            id=str(uuid.uuid4()),
            task_id="",
            name="Test Subtask",
            description="Description"
        ).validate()

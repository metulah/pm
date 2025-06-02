import uuid
import pytest
from pm.models import Note, Project, Task, TaskStatus
from pm.storage import (
    init_db, create_project, create_task,
    create_note, get_note, update_note, delete_note, list_notes
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


def test_create_project_note(db, project):
    """Test creating a note for a project."""
    note = Note(
        id=str(uuid.uuid4()),
        content="Test project note",
        author="test_user",
        entity_type="project",
        entity_id=project.id
    )
    created_note = create_note(db, note)
    assert created_note.id == note.id
    assert created_note.content == note.content
    assert created_note.author == note.author
    assert created_note.entity_type == "project"
    assert created_note.entity_id == project.id


def test_create_task_note(db, task):
    """Test creating a note for a task."""
    note = Note(
        id=str(uuid.uuid4()),
        content="Test task note",
        author="test_user",
        entity_type="task",
        entity_id=task.id
    )
    created_note = create_note(db, note)
    assert created_note.id == note.id
    assert created_note.content == note.content
    assert created_note.author == note.author
    assert created_note.entity_type == "task"
    assert created_note.entity_id == task.id


def test_get_note(db, project):
    """Test retrieving a note by ID."""
    note = Note(
        id=str(uuid.uuid4()),
        content="Test note",
        author="test_user",
        entity_type="project",
        entity_id=project.id
    )
    create_note(db, note)

    retrieved_note = get_note(db, note.id)
    assert retrieved_note is not None
    assert retrieved_note.id == note.id
    assert retrieved_note.content == note.content
    assert retrieved_note.author == note.author


def test_update_note(db, project):
    """Test updating a note."""
    note = Note(
        id=str(uuid.uuid4()),
        content="Original content",
        author="original_author",
        entity_type="project",
        entity_id=project.id
    )
    create_note(db, note)

    updated_note = update_note(
        db, note.id, content="Updated content", author="new_author")
    assert updated_note is not None
    assert updated_note.content == "Updated content"
    assert updated_note.author == "new_author"
    assert updated_note.entity_type == note.entity_type
    assert updated_note.entity_id == note.entity_id


def test_delete_note(db, project):
    """Test deleting a note."""
    note = Note(
        id=str(uuid.uuid4()),
        content="Test note",
        author="test_user",
        entity_type="project",
        entity_id=project.id
    )
    create_note(db, note)

    success = delete_note(db, note.id)
    assert success is True

    deleted_note = get_note(db, note.id)
    assert deleted_note is None


def test_list_project_notes(db, project):
    """Test listing notes for a project."""
    notes = [
        Note(
            id=str(uuid.uuid4()),
            content=f"Project note {i}",
            author="test_user",
            entity_type="project",
            entity_id=project.id
        ) for i in range(3)
    ]

    for note in notes:
        create_note(db, note)

    project_notes = list_notes(db, "project", project.id)
    assert len(project_notes) == 3
    assert all(n.entity_type == "project" for n in project_notes)
    assert all(n.entity_id == project.id for n in project_notes)


def test_list_task_notes(db, task):
    """Test listing notes for a task."""
    notes = [
        Note(
            id=str(uuid.uuid4()),
            content=f"Task note {i}",
            author="test_user",
            entity_type="task",
            entity_id=task.id
        ) for i in range(3)
    ]

    for note in notes:
        create_note(db, note)

    task_notes = list_notes(db, "task", task.id)
    assert len(task_notes) == 3
    assert all(n.entity_type == "task" for n in task_notes)
    assert all(n.entity_id == task.id for n in task_notes)


def test_note_validation(db):
    """Test note validation."""
    with pytest.raises(ValueError, match="Note content cannot be empty"):
        Note(
            id=str(uuid.uuid4()),
            content="",
            entity_type="task",
            entity_id="123"
        ).validate()

    with pytest.raises(ValueError, match="Entity type must be 'task' or 'project'"):
        Note(
            id=str(uuid.uuid4()),
            content="Test note",
            entity_type="invalid",
            entity_id="123"
        ).validate()

    with pytest.raises(ValueError, match="Entity ID cannot be empty"):
        Note(
            id=str(uuid.uuid4()),
            content="Test note",
            entity_type="task",
            entity_id=""
        ).validate()

import uuid
import pytest
from pm.models import Project, Task, TaskStatus, TaskTemplate, SubtaskTemplate
from pm.storage import (
    init_db, create_project, create_task,
    create_task_template, get_task_template, update_task_template,
    delete_task_template, list_task_templates,
    create_subtask_template, get_subtask_template, update_subtask_template,
    delete_subtask_template, list_subtask_templates,
    apply_template_to_task
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


@pytest.fixture
def template(db):
    """Create a test task template."""
    template = TaskTemplate(
        id=str(uuid.uuid4()),
        name="Test Template",
        description="A test template"
    )
    return create_task_template(db, template)


def test_create_task_template(db):
    """Test creating a task template."""
    template = TaskTemplate(
        id=str(uuid.uuid4()),
        name="Test Template",
        description="A test template"
    )
    created_template = create_task_template(db, template)
    assert created_template.id == template.id
    assert created_template.name == "Test Template"
    assert created_template.description == "A test template"


def test_get_task_template(db):
    """Test retrieving a task template by ID."""
    template = TaskTemplate(
        id=str(uuid.uuid4()),
        name="Test Template",
        description="A test template"
    )
    create_task_template(db, template)

    retrieved_template = get_task_template(db, template.id)
    assert retrieved_template is not None
    assert retrieved_template.id == template.id
    assert retrieved_template.name == template.name
    assert retrieved_template.description == template.description


def test_update_task_template(db):
    """Test updating a task template."""
    template = TaskTemplate(
        id=str(uuid.uuid4()),
        name="Original Name",
        description="Original description"
    )
    create_task_template(db, template)

    updated_template = update_task_template(
        db, template.id,
        name="Updated Name",
        description="Updated description"
    )
    assert updated_template is not None
    assert updated_template.name == "Updated Name"
    assert updated_template.description == "Updated description"


def test_delete_task_template(db):
    """Test deleting a task template."""
    template = TaskTemplate(
        id=str(uuid.uuid4()),
        name="Test Template",
        description="A test template"
    )
    create_task_template(db, template)

    success = delete_task_template(db, template.id)
    assert success is True

    deleted_template = get_task_template(db, template.id)
    assert deleted_template is None


def test_list_task_templates(db):
    """Test listing task templates."""
    templates = [
        TaskTemplate(
            id=str(uuid.uuid4()),
            name=f"Template {i}",
            description=f"Description {i}"
        ) for i in range(3)
    ]

    for template in templates:
        create_task_template(db, template)

    template_list = list_task_templates(db)
    assert len(template_list) == 3


def test_create_subtask_template(db, template):
    """Test creating a subtask template."""
    subtask = SubtaskTemplate(
        id=str(uuid.uuid4()),
        template_id=template.id,
        name="Test Subtask Template",
        description="A test subtask template",
        required_for_completion=True
    )
    created_subtask = create_subtask_template(db, subtask)
    assert created_subtask.id == subtask.id
    assert created_subtask.template_id == template.id
    assert created_subtask.name == "Test Subtask Template"
    assert created_subtask.description == "A test subtask template"
    assert created_subtask.required_for_completion is True


def test_get_subtask_template(db, template):
    """Test retrieving a subtask template by ID."""
    subtask = SubtaskTemplate(
        id=str(uuid.uuid4()),
        template_id=template.id,
        name="Test Subtask Template",
        description="A test subtask template",
        required_for_completion=True
    )
    create_subtask_template(db, subtask)

    retrieved_subtask = get_subtask_template(db, subtask.id)
    assert retrieved_subtask is not None
    assert retrieved_subtask.id == subtask.id
    assert retrieved_subtask.name == subtask.name
    assert retrieved_subtask.description == subtask.description
    assert retrieved_subtask.required_for_completion == subtask.required_for_completion


def test_update_subtask_template(db, template):
    """Test updating a subtask template."""
    subtask = SubtaskTemplate(
        id=str(uuid.uuid4()),
        template_id=template.id,
        name="Original Name",
        description="Original description",
        required_for_completion=True
    )
    create_subtask_template(db, subtask)

    updated_subtask = update_subtask_template(
        db, subtask.id,
        name="Updated Name",
        description="Updated description",
        required_for_completion=False
    )
    assert updated_subtask is not None
    assert updated_subtask.name == "Updated Name"
    assert updated_subtask.description == "Updated description"
    assert updated_subtask.required_for_completion is False


def test_delete_subtask_template(db, template):
    """Test deleting a subtask template."""
    subtask = SubtaskTemplate(
        id=str(uuid.uuid4()),
        template_id=template.id,
        name="Test Subtask Template",
        description="A test subtask template",
        required_for_completion=True
    )
    create_subtask_template(db, subtask)

    success = delete_subtask_template(db, subtask.id)
    assert success is True

    deleted_subtask = get_subtask_template(db, subtask.id)
    assert deleted_subtask is None


def test_list_subtask_templates(db, template):
    """Test listing subtask templates."""
    subtasks = [
        SubtaskTemplate(
            id=str(uuid.uuid4()),
            template_id=template.id,
            name=f"Subtask Template {i}",
            description=f"Description {i}",
            required_for_completion=True
        ) for i in range(3)
    ]

    for subtask in subtasks:
        create_subtask_template(db, subtask)

    template_subtasks = list_subtask_templates(db, template_id=template.id)
    assert len(template_subtasks) == 3
    assert all(s.template_id == template.id for s in template_subtasks)


def test_apply_template_to_task(db, task, template):
    """Test applying a template to a task."""
    # Create subtask templates
    subtasks = [
        SubtaskTemplate(
            id=str(uuid.uuid4()),
            template_id=template.id,
            name=f"Subtask {i}",
            description=f"Description {i}",
            # alternate between True and False
            required_for_completion=bool(i % 2)
        ) for i in range(3)
    ]

    for subtask in subtasks:
        create_subtask_template(db, subtask)

    # Apply template to task
    created_subtasks = apply_template_to_task(db, task.id, template.id)
    assert len(created_subtasks) == 3

    # Verify created subtasks
    for i, subtask in enumerate(created_subtasks):
        assert subtask.task_id == task.id
        assert subtask.name == f"Subtask {i}"
        assert subtask.description == f"Description {i}"
        assert subtask.required_for_completion == bool(i % 2)
        assert subtask.status == TaskStatus.NOT_STARTED


def test_template_validation(db):
    """Test template validation."""
    # Test empty name
    with pytest.raises(ValueError, match="Template name cannot be empty"):
        TaskTemplate(
            id=str(uuid.uuid4()),
            name="",
            description="Description"
        ).validate()

    # Test name too long
    with pytest.raises(ValueError, match="Template name cannot exceed 100 characters"):
        TaskTemplate(
            id=str(uuid.uuid4()),
            name="x" * 101,
            description="Description"
        ).validate()


def test_subtask_template_validation(db, template):
    """Test subtask template validation."""
    # Test empty name
    with pytest.raises(ValueError, match="Subtask template name cannot be empty"):
        SubtaskTemplate(
            id=str(uuid.uuid4()),
            template_id=template.id,
            name="",
            description="Description"
        ).validate()

    # Test name too long
    with pytest.raises(ValueError, match="Subtask template name cannot exceed 100 characters"):
        SubtaskTemplate(
            id=str(uuid.uuid4()),
            template_id=template.id,
            name="x" * 101,
            description="Description"
        ).validate()

    # Test missing template_id
    with pytest.raises(ValueError, match="Subtask template must be associated with a task template"):
        SubtaskTemplate(
            id=str(uuid.uuid4()),
            template_id="",
            name="Test Subtask Template",
            description="Description"
        ).validate()

"""Template storage operations."""

import sqlite3
import uuid
from typing import Optional, List

from ..models import TaskTemplate, SubtaskTemplate, Subtask, TaskStatus


def create_task_template(conn: sqlite3.Connection, template: TaskTemplate) -> TaskTemplate:
    """Create a new task template."""
    template.validate()
    with conn:
        conn.execute(
            """INSERT INTO task_templates (
                id, name, description, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?)""",
            (template.id, template.name, template.description,
             template.created_at, template.updated_at)
        )
    return template


def get_task_template(conn: sqlite3.Connection, template_id: str) -> Optional[TaskTemplate]:
    """Get a task template by ID."""
    row = conn.execute(
        "SELECT * FROM task_templates WHERE id = ?", (template_id,)).fetchone()
    if not row:
        return None
    return TaskTemplate(
        id=row['id'],
        name=row['name'],
        description=row['description'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


def update_task_template(conn: sqlite3.Connection, template_id: str, **kwargs) -> Optional[TaskTemplate]:
    """Update a task template's attributes."""
    template = get_task_template(conn, template_id)
    if not template:
        return None

    for key, value in kwargs.items():
        if hasattr(template, key):
            setattr(template, key, value)

    template.validate()

    with conn:
        conn.execute(
            """UPDATE task_templates SET
                name = ?, description = ?, updated_at = ?
            WHERE id = ?""",
            (template.name, template.description,
             template.updated_at, template.id)
        )
    return template


def delete_task_template(conn: sqlite3.Connection, template_id: str) -> bool:
    """Delete a task template by ID."""
    with conn:
        cursor = conn.execute(
            "DELETE FROM task_templates WHERE id = ?", (template_id,))
    return cursor.rowcount > 0


def list_task_templates(conn: sqlite3.Connection) -> List[TaskTemplate]:
    """List all task templates."""
    rows = conn.execute(
        "SELECT * FROM task_templates ORDER BY name").fetchall()
    return [
        TaskTemplate(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows
    ]


def create_subtask_template(conn: sqlite3.Connection, template: SubtaskTemplate) -> SubtaskTemplate:
    """Create a new subtask template."""
    template.validate()
    with conn:
        conn.execute(
            """INSERT INTO subtask_templates (
                id, template_id, name, description, required_for_completion
            ) VALUES (?, ?, ?, ?, ?)""",
            (template.id, template.template_id, template.name,
             template.description, 1 if template.required_for_completion else 0)
        )
    return template


def get_subtask_template(conn: sqlite3.Connection, template_id: str) -> Optional[SubtaskTemplate]:
    """Get a subtask template by ID."""
    row = conn.execute(
        "SELECT * FROM subtask_templates WHERE id = ?", (template_id,)).fetchone()
    if not row:
        return None
    return SubtaskTemplate(
        id=row['id'],
        template_id=row['template_id'],
        name=row['name'],
        description=row['description'],
        required_for_completion=bool(row['required_for_completion'])
    )


def update_subtask_template(conn: sqlite3.Connection, template_id: str, **kwargs) -> Optional[SubtaskTemplate]:
    """Update a subtask template's attributes."""
    template = get_subtask_template(conn, template_id)
    if not template:
        return None

    for key, value in kwargs.items():
        if hasattr(template, key):
            setattr(template, key, value)

    template.validate()

    with conn:
        conn.execute(
            """UPDATE subtask_templates SET
                template_id = ?, name = ?, description = ?,
                required_for_completion = ?
            WHERE id = ?""",
            (template.template_id, template.name, template.description,
             1 if template.required_for_completion else 0, template.id)
        )
    return template


def delete_subtask_template(conn: sqlite3.Connection, template_id: str) -> bool:
    """Delete a subtask template by ID."""
    with conn:
        cursor = conn.execute(
            "DELETE FROM subtask_templates WHERE id = ?", (template_id,))
    return cursor.rowcount > 0


def list_subtask_templates(conn: sqlite3.Connection, template_id: Optional[str] = None) -> List[SubtaskTemplate]:
    """List subtask templates with optional filtering."""
    query = "SELECT * FROM subtask_templates"
    params = []

    if template_id:
        query += " WHERE template_id = ?"
        params.append(template_id)

    query += " ORDER BY name"

    rows = conn.execute(query, params).fetchall()
    return [
        SubtaskTemplate(
            id=row['id'],
            template_id=row['template_id'],
            name=row['name'],
            description=row['description'],
            required_for_completion=bool(row['required_for_completion'])
        ) for row in rows
    ]


def apply_template_to_task(conn: sqlite3.Connection, task_id: str, template_id: str) -> List[Subtask]:
    """Apply a task template to create subtasks for a task."""
    # Verify task exists
    from .task import get_task  # Import here to avoid circular imports
    task = get_task(conn, task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")

    # Get template and its subtasks
    template = get_task_template(conn, template_id)
    if not template:
        raise ValueError(f"Template {template_id} not found")

    subtask_templates = list_subtask_templates(conn, template_id)
    created_subtasks = []

    # Create subtasks from template
    for st in subtask_templates:
        subtask = Subtask(
            id=str(uuid.uuid4()),
            task_id=task_id,
            name=st.name,
            description=st.description,
            required_for_completion=st.required_for_completion,
            status=TaskStatus.NOT_STARTED
        )
        from .subtask import create_subtask  # Import here to avoid circular imports
        created_subtasks.append(create_subtask(conn, subtask))

    return created_subtasks

"""Task storage operations."""

import sqlite3
from typing import Optional, List, Set

from ..models import Task, TaskStatus


def create_task(conn: sqlite3.Connection, task: Task) -> Task:
    """Create a new task in the database."""
    task.validate()
    with conn:
        conn.execute(
            "INSERT INTO tasks (id, project_id, name, description, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (task.id, task.project_id, task.name, task.description,
             task.status.value, task.created_at, task.updated_at)
        )
    return task


def get_task(conn: sqlite3.Connection, task_id: str) -> Optional[Task]:
    """Get a task by ID."""
    row = conn.execute("SELECT * FROM tasks WHERE id = ?",
                       (task_id,)).fetchone()
    if not row:
        return None
    return Task(
        id=row['id'],
        project_id=row['project_id'],
        name=row['name'],
        description=row['description'],
        status=TaskStatus(row['status']),
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


def update_task(conn: sqlite3.Connection, task_id: str, **kwargs) -> Optional[Task]:
    """Update a task's attributes."""
    task = get_task(conn, task_id)
    if not task:
        return None

    # Store original status for comparison
    original_status = task.status

    for key, value in kwargs.items():
        if hasattr(task, key):
            if key == 'status' and not isinstance(value, TaskStatus):
                value = TaskStatus(value)
            setattr(task, key, value)

    # If trying to mark as COMPLETED, check required subtasks
    if task.status == TaskStatus.COMPLETED and original_status != TaskStatus.COMPLETED:
        # Check if all required subtasks are completed
        from .subtask import list_subtasks  # Import here to avoid circular imports
        subtasks = list_subtasks(conn, task_id)
        incomplete_required = [s for s in subtasks
                               if s.required_for_completion and s.status != TaskStatus.COMPLETED]
        if incomplete_required:
            names = ", ".join(s.name for s in incomplete_required)
            raise ValueError(
                f"Cannot mark task as COMPLETED. Required subtasks not completed: {names}")

    # Validate status transition
    if original_status != task.status:
        valid_transitions = {
            TaskStatus.NOT_STARTED: {TaskStatus.IN_PROGRESS},
            TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.BLOCKED, TaskStatus.PAUSED},
            TaskStatus.BLOCKED: {TaskStatus.IN_PROGRESS},
            TaskStatus.PAUSED: {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED},
            TaskStatus.COMPLETED: set()  # No transitions allowed from COMPLETED
        }
        if task.status not in valid_transitions.get(original_status, set()):
            raise ValueError(
                f"Invalid status transition: {original_status.value} -> {task.status.value}")

    task.validate()

    with conn:
        conn.execute(
            "UPDATE tasks SET project_id = ?, name = ?, description = ?, status = ?, updated_at = ? WHERE id = ?",
            (task.project_id, task.name, task.description,
             task.status.value, task.updated_at, task.id)
        )
    return task


def delete_task(conn: sqlite3.Connection, task_id: str) -> bool:
    """Delete a task by ID."""
    with conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cursor.rowcount > 0


def list_tasks(conn: sqlite3.Connection, project_id: Optional[str] = None, status: Optional[TaskStatus] = None) -> List[Task]:
    """List tasks with optional filtering."""
    query = "SELECT * FROM tasks"
    params = []

    if project_id or status:
        query += " WHERE"

    if project_id:
        query += " project_id = ?"
        params.append(project_id)

    if status:
        if project_id:
            query += " AND"
        query += " status = ?"
        params.append(status.value)

    query += " ORDER BY name"

    rows = conn.execute(query, params).fetchall()
    return [
        Task(
            id=row['id'],
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'],
            status=TaskStatus(row['status']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows
    ]


def add_task_dependency(conn: sqlite3.Connection, task_id: str, dependency_id: str) -> bool:
    """Add a dependency between tasks."""
    # Validate both tasks exist
    task = get_task(conn, task_id)
    dependency = get_task(conn, dependency_id)
    if not task or not dependency:
        return False

    # Prevent self-dependency
    if task_id == dependency_id:
        raise ValueError("A task cannot depend on itself")

    # Check for circular dependencies
    if has_circular_dependency(conn, dependency_id, task_id):
        raise ValueError(
            "Adding this dependency would create a circular reference")

    try:
        with conn:
            conn.execute(
                "INSERT INTO task_dependencies (task_id, dependency_id) VALUES (?, ?)",
                (task_id, dependency_id)
            )
        return True
    except sqlite3.IntegrityError:
        # Dependency already exists
        return False


def remove_task_dependency(conn: sqlite3.Connection, task_id: str, dependency_id: str) -> bool:
    """Remove a dependency between tasks."""
    with conn:
        cursor = conn.execute(
            "DELETE FROM task_dependencies WHERE task_id = ? AND dependency_id = ?",
            (task_id, dependency_id)
        )
    return cursor.rowcount > 0


def get_task_dependencies(conn: sqlite3.Connection, task_id: str) -> List[Task]:
    """Get all dependencies for a task."""
    rows = conn.execute(
        "SELECT t.* FROM tasks t JOIN task_dependencies td ON t.id = td.dependency_id WHERE td.task_id = ?",
        (task_id,)
    ).fetchall()
    return [
        Task(
            id=row['id'],
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'],
            status=TaskStatus(row['status']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows
    ]


def has_circular_dependency(conn: sqlite3.Connection, task_id: str, potential_dependency_id: str, visited: Optional[Set[str]] = None) -> bool:
    """Check if adding a dependency would create a circular reference."""
    if visited is None:
        visited = set()

    if task_id in visited:
        return False

    visited.add(task_id)

    # If the task directly depends on the potential dependency, it would create a circle
    if task_id == potential_dependency_id:
        return True

    # Check all dependencies of the task
    for row in conn.execute(
        "SELECT dependency_id FROM task_dependencies WHERE task_id = ?",
        (task_id,)
    ):
        dependency_id = row[0]
        if has_circular_dependency(conn, dependency_id, potential_dependency_id, visited):
            return True

    return False

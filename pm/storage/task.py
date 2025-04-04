"""Task storage operations."""

import sqlite3
from typing import Optional, List, Set
import datetime  # Added for updated_at in update_task

from ..models import Task, TaskStatus
from ..core.utils import generate_slug  # Import slug generator
# Removed top-level import: from .project import get_project


def _find_unique_task_slug(conn: sqlite3.Connection, project_id: str, base_slug: str) -> str:
    """Finds a unique task slug within a project, appending numbers if necessary."""
    slug = base_slug
    counter = 1
    while True:
        row = conn.execute(
            "SELECT id FROM tasks WHERE project_id = ? AND slug = ?",
            (project_id, slug)
        ).fetchone()
        if not row:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def create_task(conn: sqlite3.Connection, task: Task) -> Task:
    """Create a new task in the database, generating a unique slug within the project."""
    task.validate()
    base_slug = generate_slug(task.name)
    task.slug = _find_unique_task_slug(
        conn, task.project_id, base_slug)  # Assign unique slug

    with conn:
        conn.execute(
            "INSERT INTO tasks (id, project_id, name, description, status, slug, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (task.id, task.project_id, task.name, task.description,
             task.status.value, task.slug, task.created_at, task.updated_at)
        )
    return task


def get_task(conn: sqlite3.Connection, task_id: str) -> Optional[Task]:
    """Get a task by ID."""
    row = conn.execute("SELECT * FROM tasks WHERE id = ?",
                       (task_id,)).fetchone()
    if not row:
        return None
    # Ensure all columns are present before creating the object
    # This assumes the SELECT * includes the new 'slug' column
    return Task(
        id=row['id'],
        project_id=row['project_id'],
        name=row['name'],
        description=row['description'],
        status=TaskStatus(row['status']),
        slug=row['slug'],  # Populate slug
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


def get_task_by_slug(conn: sqlite3.Connection, project_id: str, slug: str) -> Optional[Task]:
    """Get a task by its slug within a specific project."""
    row = conn.execute(
        "SELECT * FROM tasks WHERE project_id = ? AND slug = ?",
        (project_id, slug)
    ).fetchone()
    if not row:
        return None
    # Re-use the same instantiation logic as get_task
    return Task(
        id=row['id'],
        project_id=row['project_id'],
        name=row['name'],
        description=row['description'],
        status=TaskStatus(row['status']),
        slug=row['slug'],
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

    # Validate target project if project_id is being changed
    if 'project_id' in kwargs:
        from .project import get_project  # Import get_project inside the function
        new_project_id = kwargs['project_id']
        if new_project_id != task.project_id:  # Only validate if it's actually changing
            target_project = get_project(conn, new_project_id)
            if not target_project:
                raise ValueError(
                    f"Target project '{new_project_id}' not found.")

    # Apply updates
    for key, value in kwargs.items():
        if hasattr(task, key):
            if key == 'status' and not isinstance(value, TaskStatus):
                value = TaskStatus(value)
            # Ensure project_id is only set if it exists in kwargs (already validated above)
            if key == 'project_id' and key not in kwargs:
                continue
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

    task.updated_at = datetime.datetime.now()  # Ensure updated_at is set
    task.validate()

    with conn:
        # Slug is immutable, so it's not included in the UPDATE statement's SET clause
        conn.execute(
            "UPDATE tasks SET project_id = ?, name = ?, description = ?, status = ?, updated_at = ? WHERE id = ?",
            (task.project_id, task.name, task.description,
             task.status.value, task.updated_at, task.id)
        )
    # Re-fetch the task to ensure the returned object includes the slug
    # (since the 'task' object in memory might not have had it if fetched before slug was added)
    return get_task(conn, task_id)


def delete_task(conn: sqlite3.Connection, task_id: str) -> bool:
    """Delete a task by ID."""
    with conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cursor.rowcount > 0


def list_tasks(conn: sqlite3.Connection, project_id: Optional[str] = None, status: Optional[TaskStatus] = None, include_completed: bool = False) -> List[Task]:
    """List tasks with optional filtering, optionally including completed ones."""
    # Select all columns from tasks table (aliased as t)
    query = "SELECT t.* FROM tasks t"
    params = []
    conditions = []

    if project_id:
        # Qualify project_id with table alias 't'
        conditions.append("t.project_id = ?")
        params.append(project_id)

    # Handle status filtering:
    # - If a specific status is requested, use it.
    # - Otherwise, if include_completed is False (default), exclude COMPLETED.
    if status:
        # Qualify status with table alias 't'
        conditions.append("t.status = ?")
        params.append(status.value)
    elif not include_completed:
        # Qualify status with table alias 't'
        conditions.append("t.status != ?")
        params.append(TaskStatus.COMPLETED.value)
    # If status is None and include_completed is True, no status filter is added.

    # Join with projects table (aliased as p) to sort by project slug
    query += " JOIN projects p ON t.project_id = p.id"

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # Order by project slug, then task slug
    query += " ORDER BY p.slug, t.slug"

    rows = conn.execute(query, params).fetchall()
    tasks = []
    for row in rows:
        tasks.append(Task(
            id=row['id'],
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'],
            status=TaskStatus(row['status']),
            slug=row['slug'],  # Populate slug
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ))
    return tasks


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
    dependencies = []
    for row in rows:
        dependencies.append(Task(
            id=row['id'],
            project_id=row['project_id'],
            name=row['name'],
            description=row['description'],
            status=TaskStatus(row['status']),
            slug=row['slug'],  # Populate slug
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ))
    return dependencies


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

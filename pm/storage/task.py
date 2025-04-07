"""Task storage operations."""

import sqlite3
from typing import Optional, List, Set
import datetime  # Added for updated_at in update_task

from ..models import Task, TaskStatus
from ..core.types import ProjectStatus  # Moved import here
from ..core.utils import generate_slug
from .note import count_notes  # Import the note counting function
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
        updated_at=row['updated_at'],
        # Fetch and add note count
        note_count=count_notes(conn, 'task', row['id'])
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
        updated_at=row['updated_at'],
        # Fetch and add note count
        note_count=count_notes(conn, 'task', row['id'])
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
            # Added ABANDONED as a possible target state
            TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.BLOCKED, TaskStatus.PAUSED, TaskStatus.ABANDONED},
            TaskStatus.BLOCKED: {TaskStatus.IN_PROGRESS, TaskStatus.ABANDONED},
            TaskStatus.PAUSED: {TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED, TaskStatus.ABANDONED},
            TaskStatus.COMPLETED: set(),  # No transitions allowed from COMPLETED
            TaskStatus.ABANDONED: set()   # No transitions allowed from ABANDONED
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


# Add force flag for consistency, though not strictly needed by CLI yet
def delete_task(conn: sqlite3.Connection, task_id: str, force: bool = False) -> bool:
    """Delete a task by ID, including associated data."""
    # Note: The CLI layer currently ensures --force is used for task delete,
    # so the 'force' flag here is mainly for potential direct storage layer use
    # and consistency with project delete. The actual deletion logic runs regardless.

    # Check if any other tasks depend on this task
    dependents_cursor = conn.execute(
        "SELECT task_id FROM task_dependencies WHERE dependency_id = ?",
        (task_id,)
    )
    dependent_task_ids = [row[0] for row in dependents_cursor.fetchall()]

    if dependent_task_ids:
        # Fetch slugs for better error message (optional but helpful)
        # Note: This could be optimized, but is clearer for an error message
        dependent_slugs = []
        for dep_id in dependent_task_ids:
            task = get_task(conn, dep_id)  # Re-use existing get_task
            if task and task.slug:
                dependent_slugs.append(f"'{task.slug}' (ID: {dep_id})")
            else:
                # Fallback if task/slug not found
                dependent_slugs.append(f"ID: {dep_id}")

        raise ValueError(
            f"Cannot delete task (ID: {task_id}). It is a dependency for other tasks: {', '.join(dependent_slugs)}. "
            "Remove these dependencies first."
        )
        # TODO: Consider if --force should bypass this check. Currently, it does not.
        # TODO: Consider removing ON DELETE CASCADE from the dependency_id FK in db.py
        #       for database-level enforcement, though this requires schema migration.

    # If no dependents found, proceed with deletion
    with conn:
        # Explicitly delete associated data first
        # 1. Notes
        conn.execute(
            "DELETE FROM notes WHERE entity_type = 'task' AND entity_id = ?",
            (task_id,)
        )
        # 2. Metadata
        conn.execute(
            "DELETE FROM task_metadata WHERE task_id = ?",
            (task_id,)
        )
        # 3. Dependencies (where this task is either the task or the dependency)
        conn.execute(
            "DELETE FROM task_dependencies WHERE task_id = ? OR dependency_id = ?",
            (task_id, task_id)
        )
        # 4. Subtasks
        conn.execute(
            "DELETE FROM subtasks WHERE task_id = ?",
            (task_id,)
        )

        # 5. Finally, delete the task itself
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cursor.rowcount > 0


def list_tasks(conn: sqlite3.Connection, project_id: Optional[str] = None, status: Optional[TaskStatus] = None, include_completed: bool = False, include_abandoned: bool = False, include_inactive_project_tasks: bool = False) -> List[Task]:
    """List tasks with optional filtering, optionally including completed, abandoned tasks and tasks from inactive projects."""
    # Select all columns from tasks table (aliased as t)
    query = "SELECT t.* FROM tasks t"
    params = []
    conditions = []

    # ProjectStatus import moved to top

    # --- Project Filtering ---
    if project_id:
        # Filter by specific project ID
        conditions.append("t.project_id = ?")
        params.append(project_id)
    elif not include_inactive_project_tasks:
        # If no specific project requested and not including inactive,
        # filter to only show tasks from ACTIVE projects.
        conditions.append("p.status = ?")
        params.append(ProjectStatus.ACTIVE.value)
    # If project_id is None and include_inactive_project_tasks is True, no project filter is added.

    # --- Task Status Filtering (applied independently) ---
    if status:
        # Filter by specific task status if provided
        conditions.append("t.status = ?")
        params.append(status.value)
    else:
        # If no specific status is requested, apply default filters
        default_exclude_statuses = []
        if not include_completed:
            default_exclude_statuses.append(TaskStatus.COMPLETED.value)
        if not include_abandoned:
            default_exclude_statuses.append(TaskStatus.ABANDONED.value)

        if default_exclude_statuses:
            placeholders = ', '.join('?' for _ in default_exclude_statuses)
            conditions.append(f"t.status NOT IN ({placeholders})")
            params.extend(default_exclude_statuses)
    # If status is provided, or if both include_completed and include_abandoned are True, no default status filter is added.

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
            updated_at=row['updated_at'],
            # Fetch and add note count
            note_count=count_notes(conn, 'task', row['id'])
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

"""Project storage operations."""

import sqlite3
import datetime
from typing import Optional, List
from ..models import Project
# Removed top-level import: from .task import list_tasks


class ProjectNotEmptyError(Exception):
    """Raised when attempting to delete a project that still contains tasks."""
    pass


def create_project(conn: sqlite3.Connection, project: Project) -> Project:
    """Create a new project in the database."""
    project.validate()
    with conn:
        conn.execute(
            "INSERT INTO projects (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (project.id, project.name, project.description,
             project.created_at, project.updated_at)
        )
    return project


def get_project(conn: sqlite3.Connection, project_id: str) -> Optional[Project]:
    """Get a project by ID."""
    row = conn.execute("SELECT * FROM projects WHERE id = ?",
                       (project_id,)).fetchone()
    if not row:
        return None
    return Project(
        id=row['id'],
        name=row['name'],
        description=row['description'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


def update_project(conn: sqlite3.Connection, project_id: str, **kwargs) -> Optional[Project]:
    """Update a project's attributes."""
    project = get_project(conn, project_id)
    if not project:
        return None

    for key, value in kwargs.items():
        if hasattr(project, key):
            setattr(project, key, value)

    project.updated_at = datetime.datetime.now()
    project.validate()

    with conn:
        conn.execute(
            "UPDATE projects SET name = ?, description = ?, updated_at = ? WHERE id = ?",
            (project.name, project.description, project.updated_at, project.id)
        )
    return project


def delete_project(conn: sqlite3.Connection, project_id: str) -> bool:
    """Delete a project by ID after checking for tasks."""
    from .task import list_tasks  # Import list_tasks inside the function
    # Check for existing tasks in this project
    tasks = list_tasks(conn, project_id=project_id)
    if tasks:
        raise ProjectNotEmptyError(
            f"Cannot delete project '{project_id}' because it still contains {len(tasks)} task(s)."
        )

    # Proceed with deletion if no tasks found
    with conn:
        cursor = conn.execute(
            "DELETE FROM projects WHERE id = ?", (project_id,)
        )
    return cursor.rowcount > 0


def list_projects(conn: sqlite3.Connection) -> List[Project]:
    """List all projects."""
    rows = conn.execute("SELECT * FROM projects ORDER BY name").fetchall()
    return [
        Project(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows
    ]

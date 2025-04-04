"""Project storage operations."""

import sqlite3
import datetime
from typing import Optional, List
from ..models import Project
from ..core.types import ProjectStatus  # Import ProjectStatus
import sys  # Import sys for debug print
# Removed top-level import: from .task import list_tasks


class ProjectNotEmptyError(Exception):
    """Raised when attempting to delete a project that still contains tasks."""
    pass


def create_project(conn: sqlite3.Connection, project: Project) -> Project:
    """Create a new project in the database."""
    project.validate()
    with conn:
        conn.execute(
            "INSERT INTO projects (id, name, description, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (project.id, project.name, project.description, project.status.value,
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
        status=ProjectStatus(row['status']),  # Add status
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
            # Handle enum conversion for status
            if key == 'status' and not isinstance(value, ProjectStatus):
                value = ProjectStatus(value)
            setattr(project, key, value)

    project.updated_at = datetime.datetime.now()
    project.validate()

    with conn:
        conn.execute(
            "UPDATE projects SET name = ?, description = ?, status = ?, updated_at = ? WHERE id = ?",
            (project.name, project.description,
             project.status.value, project.updated_at, project.id)
        )
    return project


def delete_project(conn: sqlite3.Connection, project_id: str, force: bool = False) -> bool:
    """Delete a project by ID. If force is True, deletes associated tasks first."""
    # Imports moved inside function to avoid circular dependency issues
    from .task import list_tasks, delete_task

    tasks = list_tasks(conn, project_id=project_id)

    if tasks:
        if force:
            # Force delete: Delete associated tasks first
            # Use a transaction for task deletion for atomicity (optional but good practice)
            with conn:
                for task in tasks:
                    # We might want more robust error handling here in the future
                    # e.g., log failures but continue? For now, assume success or let it fail.
                    delete_task(conn, task.id)
            # Proceed to delete project after tasks are deleted
        else:
            # Not forcing and tasks exist: Raise error
            raise ProjectNotEmptyError(
                f"Cannot delete project '{project_id}' because it still contains {len(tasks)} task(s). Use --force to delete anyway."
            )
    # Else: No tasks found, or tasks were deleted because force=True

    # Proceed with project deletion
    with conn:
        cursor = conn.execute(
            "DELETE FROM projects WHERE id = ?", (project_id,))

    # Return True if the project was found and deleted (rowcount > 0)
    # This is true even if force=True and tasks were deleted first.
    # It returns False only if the project ID didn't exist initially.
    return cursor.rowcount > 0


def list_projects(conn: sqlite3.Connection) -> List[Project]:
    """List all projects."""
    rows = conn.execute("SELECT * FROM projects ORDER BY name").fetchall()
    projects = []
    for row in rows:
        try:
            # --- Add Debug Print ---
            print(
                f"DEBUG[list_projects]: Processing row with keys: {row.keys()}", file=sys.stderr)
            # --- End Debug Print ---
            project = Project(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                status=ProjectStatus(row['status']),  # Add status
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            projects.append(project)
        except IndexError as e:
            print(
                f"DEBUG[list_projects]: IndexError creating Project from row: {dict(row)}. Error: {e}", file=sys.stderr)
            # Optionally re-raise or handle differently
            raise
    return projects

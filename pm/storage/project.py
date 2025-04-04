"""Project storage operations."""

import sqlite3
import datetime
from typing import Optional, List
from ..models import Project
from ..core.types import ProjectStatus
from ..core.utils import generate_slug  # Import slug generator
import sys
# Removed top-level import: from .task import list_tasks


class ProjectNotEmptyError(Exception):
    """Raised when attempting to delete a project that still contains tasks."""
    pass


def _find_unique_project_slug(conn: sqlite3.Connection, base_slug: str) -> str:
    """Finds a unique slug, appending numbers if necessary."""
    slug = base_slug
    counter = 1
    while True:
        row = conn.execute(
            "SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not row:
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


def create_project(conn: sqlite3.Connection, project: Project) -> Project:
    """Create a new project in the database, generating a unique slug."""
    project.validate()
    base_slug = generate_slug(project.name)
    project.slug = _find_unique_project_slug(
        conn, base_slug)  # Assign unique slug

    with conn:
        conn.execute(
            "INSERT INTO projects (id, name, description, status, slug, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project.id, project.name, project.description, project.status.value,
             project.slug, project.created_at, project.updated_at)
        )
    return project


def get_project(conn: sqlite3.Connection, project_id: str) -> Optional[Project]:
    """Get a project by ID."""
    row = conn.execute("SELECT * FROM projects WHERE id = ?",
                       (project_id,)).fetchone()
    if not row:
        return None
    # Ensure all columns are present before creating the object
    # This assumes the SELECT * includes the new 'slug' column
    return Project(
        id=row['id'],
        name=row['name'],
        description=row['description'],
        status=ProjectStatus(row['status']),
        slug=row['slug'],  # Populate slug
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


def get_project_by_slug(conn: sqlite3.Connection, slug: str) -> Optional[Project]:
    """Get a project by its unique slug."""
    row = conn.execute(
        "SELECT * FROM projects WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return None
    # Re-use the same instantiation logic as get_project
    return Project(
        id=row['id'],
        name=row['name'],
        description=row['description'],
        status=ProjectStatus(row['status']),
        slug=row['slug'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


def update_project(conn: sqlite3.Connection, project_id: str, **kwargs) -> Optional[Project]:
    """Update a project's attributes."""
    project = get_project(conn, project_id)
    if not project:
        return None

    original_status = project.status  # Store original status
    new_status_str = kwargs.get('status')
    new_status = ProjectStatus(new_status_str) if new_status_str else None

    # --- Status Transition Validation ---
    if new_status and new_status != original_status:
        valid_transitions = {
            ProjectStatus.ACTIVE: {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED},
            ProjectStatus.COMPLETED: {ProjectStatus.ARCHIVED},
            ProjectStatus.CANCELLED: {ProjectStatus.ARCHIVED},
            # Cannot transition from ARCHIVED (maybe to ACTIVE later?)
            ProjectStatus.ARCHIVED: set()
        }
        allowed_transitions = valid_transitions.get(original_status, set())
        if new_status not in allowed_transitions:
            raise ValueError(
                f"Invalid project status transition: {original_status.value} -> {new_status.value}")
        # If transition is valid, update the status in kwargs for application below
        kwargs['status'] = new_status  # Ensure it's the Enum type

    # --- Apply Updates ---
    for key, value in kwargs.items():
        if hasattr(project, key):
            # Status enum conversion already handled above if present
            setattr(project, key, value)
    project.updated_at = datetime.datetime.now()
    project.validate()

    with conn:
        conn.execute(
            # Slug is immutable, so it's not included in the UPDATE statement
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


def list_projects(conn: sqlite3.Connection, include_completed: bool = False, include_archived: bool = False) -> List[Project]:
    """List projects, filtering by status based on flags."""
    query = "SELECT * FROM projects"
    params = []
    conditions = []

    # Determine which statuses to include based on flags
    # Always include ACTIVE by default
    included_statuses = {ProjectStatus.ACTIVE}
    if include_completed:
        included_statuses.add(ProjectStatus.COMPLETED)
    if include_archived:
        included_statuses.add(ProjectStatus.ARCHIVED)
        # Include CANCELLED when showing ARCHIVED
        included_statuses.add(ProjectStatus.CANCELLED)

    # Build the WHERE clause using IN operator
    if len(included_statuses) < len(ProjectStatus):  # Only add WHERE if not showing all
        # Create placeholders for each status value
        placeholders = ', '.join('?' for _ in included_statuses)
        conditions.append(f"status IN ({placeholders})")
        params.extend([s.value for s in included_statuses])

    if conditions:
        # Though only one condition here
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY name"  # Keep sorting by name
    rows = conn.execute(query, params).fetchall()
    projects = []
    for row in rows:
        try:
            # Debug print removed
            project = Project(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                status=ProjectStatus(row['status']),
                slug=row['slug'],  # Populate slug
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

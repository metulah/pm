"""Subtask storage operations."""

import sqlite3
from typing import Optional, List

from ..models import Subtask, TaskStatus


def create_subtask(conn: sqlite3.Connection, subtask: Subtask) -> Subtask:
    """Create a new subtask."""
    subtask.validate()
    with conn:
        conn.execute(
            """INSERT INTO subtasks (
                id, task_id, name, description,
                required_for_completion, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (subtask.id, subtask.task_id, subtask.name,
             subtask.description, 1 if subtask.required_for_completion else 0,
             subtask.status.value, subtask.created_at, subtask.updated_at)
        )
    return subtask


def get_subtask(conn: sqlite3.Connection, subtask_id: str) -> Optional[Subtask]:
    """Get a subtask by ID."""
    row = conn.execute("SELECT * FROM subtasks WHERE id = ?",
                       (subtask_id,)).fetchone()
    if not row:
        return None
    return Subtask(
        id=row['id'],
        task_id=row['task_id'],
        name=row['name'],
        description=row['description'],
        required_for_completion=bool(row['required_for_completion']),
        status=TaskStatus(row['status']),
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


def update_subtask(conn: sqlite3.Connection, subtask_id: str, **kwargs) -> Optional[Subtask]:
    """Update a subtask's attributes."""
    subtask = get_subtask(conn, subtask_id)
    if not subtask:
        return None

    for key, value in kwargs.items():
        if hasattr(subtask, key):
            if key == 'status' and not isinstance(value, TaskStatus):
                value = TaskStatus(value)
            setattr(subtask, key, value)

    subtask.validate()

    with conn:
        conn.execute(
            """UPDATE subtasks SET
                task_id = ?, name = ?, description = ?,
                required_for_completion = ?, status = ?,
                updated_at = ?
            WHERE id = ?""",
            (subtask.task_id, subtask.name, subtask.description,
             1 if subtask.required_for_completion else 0,
             subtask.status.value, subtask.updated_at, subtask.id)
        )
    return subtask


def delete_subtask(conn: sqlite3.Connection, subtask_id: str) -> bool:
    """Delete a subtask by ID."""
    with conn:
        cursor = conn.execute(
            "DELETE FROM subtasks WHERE id = ?", (subtask_id,))
    return cursor.rowcount > 0


def list_subtasks(conn: sqlite3.Connection, task_id: Optional[str] = None, status: Optional[TaskStatus] = None) -> List[Subtask]:
    """List subtasks with optional filtering."""
    query = "SELECT * FROM subtasks"
    params = []

    if task_id or status:
        query += " WHERE"

    if task_id:
        query += " task_id = ?"
        params.append(task_id)

    if status:
        if task_id:
            query += " AND"
        query += " status = ?"
        params.append(status.value)

    query += " ORDER BY name"

    rows = conn.execute(query, params).fetchall()
    return [
        Subtask(
            id=row['id'],
            task_id=row['task_id'],
            name=row['name'],
            description=row['description'],
            required_for_completion=bool(row['required_for_completion']),
            status=TaskStatus(row['status']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows
    ]

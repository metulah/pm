"""Note storage operations."""

import sqlite3
from typing import Optional, List

from ..models import Note


def create_note(conn: sqlite3.Connection, note: Note) -> Note:
    """Create a new note."""
    note.validate()
    with conn:
        conn.execute(
            """INSERT INTO notes (
                id, content, entity_type, entity_id, author,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (note.id, note.content, note.entity_type,
             note.entity_id, note.author,
             note.created_at, note.updated_at)
        )
    return note


def get_note(conn: sqlite3.Connection, note_id: str) -> Optional[Note]:
    """Get a note by ID."""
    row = conn.execute("SELECT * FROM notes WHERE id = ?",
                       (note_id,)).fetchone()
    if not row:
        return None
    return Note(
        id=row['id'],
        content=row['content'],
        entity_type=row['entity_type'],
        entity_id=row['entity_id'],
        author=row['author'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )


def update_note(conn: sqlite3.Connection, note_id: str, **kwargs) -> Optional[Note]:
    """Update a note's attributes."""
    note = get_note(conn, note_id)
    if not note:
        return None

    for key, value in kwargs.items():
        if hasattr(note, key):
            setattr(note, key, value)

    note.validate()

    with conn:
        conn.execute(
            """UPDATE notes SET
                content = ?, entity_type = ?, entity_id = ?,
                author = ?, updated_at = ?
            WHERE id = ?""",
            (note.content, note.entity_type, note.entity_id,
             note.author, note.updated_at, note.id)
        )
    return note


def delete_note(conn: sqlite3.Connection, note_id: str) -> bool:
    """Delete a note by ID."""
    with conn:
        cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    return cursor.rowcount > 0


def list_notes(conn: sqlite3.Connection, entity_type: str, entity_id: str) -> List[Note]:
    """List notes for a task or project."""
    rows = conn.execute(
        """SELECT * FROM notes
        WHERE entity_type = ? AND entity_id = ?
        ORDER BY created_at DESC""",
        (entity_type, entity_id)
    ).fetchall()
    return [
        Note(
            id=row['id'],
            content=row['content'],
            entity_type=row['entity_type'],
            entity_id=row['entity_id'],
            author=row['author'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) for row in rows
    ]


def count_notes(conn: sqlite3.Connection, entity_type: str, entity_id: str) -> int:
    """Count notes for a specific entity (task or project)."""
    cursor = conn.execute(
        "SELECT COUNT(*) FROM notes WHERE entity_type = ? AND entity_id = ?",
        (entity_type, entity_id)
    )
    result = cursor.fetchone()
    return result[0] if result else 0

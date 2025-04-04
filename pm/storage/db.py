"""Database initialization and connection management."""

import sqlite3
import datetime
import sys


def adapt_datetime(dt):
    """Adapt datetime.datetime to ISO 8601 date string."""
    return dt.isoformat()


def convert_datetime(ts):
    """Convert ISO 8601 datetime string to datetime.datetime."""
    return datetime.datetime.fromisoformat(ts.decode())


# Register the adapter and converter
sqlite3.register_adapter(datetime.datetime, adapt_datetime)
sqlite3.register_converter("TIMESTAMP", convert_datetime)


def init_db(db_path: str = "pm.db") -> sqlite3.Connection:
    """Initialize the database and return a connection."""
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row

    # --- Schema Creation / Migration ---
    with conn:
        # Check if projects table exists and if status column is missing
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='projects';")
        table_exists = cursor.fetchone()
        status_column_exists = False
        if table_exists:
            cursor = conn.execute("PRAGMA table_info(projects);")
            columns = [row['name'] for row in cursor.fetchall()]
            status_column_exists = 'status' in columns

        # Add 'status' column to 'projects' if table exists but column doesn't
        if table_exists and not status_column_exists:
            print("INFO: Adding 'status' column to existing 'projects' table.",
                  file=sys.stderr)  # Optional info message
            conn.execute(
                "ALTER TABLE projects ADD COLUMN status TEXT NOT NULL DEFAULT 'ACTIVE';")

        # Create tables if they don't exist (original logic)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'ACTIVE', -- Add status column
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'NOT_STARTED',
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
            CHECK (status IN ('NOT_STARTED', 'IN_PROGRESS', 'BLOCKED', 'PAUSED', 'COMPLETED'))
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS task_dependencies (
            task_id TEXT NOT NULL,
            dependency_id TEXT NOT NULL,
            PRIMARY KEY (task_id, dependency_id),
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
            FOREIGN KEY (dependency_id) REFERENCES tasks (id) ON DELETE CASCADE,
            CHECK (task_id != dependency_id)
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS task_metadata (
            task_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value_type TEXT NOT NULL,
            value_string TEXT,
            value_int INTEGER,
            value_float REAL,
            value_datetime TIMESTAMP,
            value_bool INTEGER,
            value_json TEXT,
            PRIMARY KEY (task_id, key),
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
            CHECK (value_type IN ('string', 'int', 'float', 'datetime', 'bool', 'json'))
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            author TEXT,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CHECK (entity_type IN ('task', 'project'))
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS task_templates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS subtask_templates (
            id TEXT PRIMARY KEY,
            template_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            required_for_completion INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (template_id) REFERENCES task_templates (id) ON DELETE CASCADE
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS subtasks (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            required_for_completion INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'NOT_STARTED',
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE,
            CHECK (status IN ('NOT_STARTED', 'IN_PROGRESS', 'BLOCKED', 'PAUSED', 'COMPLETED'))
        )
        """)

        # Redundant migration check removed (already handled earlier)

    return conn

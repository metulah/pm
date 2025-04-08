"""Database initialization and connection management."""

import sqlite3
import datetime
import sys
import re  # For migration slug generation
import unicodedata  # For migration slug generation
from typing import Dict, Set  # For migration uniqueness tracking


def adapt_datetime(dt):
    """Adapt datetime.datetime to ISO 8601 date string."""
    return dt.isoformat()


def convert_datetime(ts):
    """Convert ISO 8601 datetime string to datetime.datetime."""
    return datetime.datetime.fromisoformat(ts.decode())


# Register the adapter and converter
sqlite3.register_adapter(datetime.datetime, adapt_datetime)
sqlite3.register_converter("TIMESTAMP", convert_datetime)
# --- Migration Helper Functions ---


def _migrate_generate_slug(name: str) -> str:
    """
    Generate a URL-friendly slug from a string (Migration specific version).
    Handles lowercasing, replacing spaces/underscores with hyphens,
    removing invalid characters, and collapsing multiple hyphens.
    """
    if not name:
        return "untitled"  # Ensure non-empty slug

    # Normalize unicode characters
    try:
        name = unicodedata.normalize('NFKD', name).encode(
            'ascii', 'ignore').decode('ascii')
    except TypeError:  # Handle cases where name might not be a string initially
        name = str(name)
        name = unicodedata.normalize('NFKD', name).encode(
            'ascii', 'ignore').decode('ascii')

    # Lowercase and replace spaces/underscores with hyphens
    name = name.lower().replace(' ', '-').replace('_', '-')

    # Remove characters that are not alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9-]+', '', name)

    # Collapse consecutive hyphens into one
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    # Ensure slug is not empty after processing
    if not slug:
        return "untitled"

    return slug


def _migrate_find_unique_project_slug(conn: sqlite3.Connection, base_slug: str, existing_slugs: Set[str]) -> str:
    """Finds a unique project slug during migration, checking against already assigned slugs."""
    slug = base_slug
    counter = 1
    while slug in existing_slugs:
        # Check DB just in case (though existing_slugs should be primary)
        row = conn.execute(
            "SELECT id FROM projects WHERE slug = ?", (slug,)).fetchone()
        if not row:
            break  # Found a gap, use it
        slug = f"{base_slug}-{counter}"
        counter += 1
    existing_slugs.add(slug)  # Add the newly assigned slug
    return slug


def _migrate_find_unique_task_slug(conn: sqlite3.Connection, project_id: str, base_slug: str, existing_task_slugs: Dict[str, Set[str]]) -> str:
    """Finds a unique task slug within a project during migration."""
    slug = base_slug
    counter = 1
    project_slugs = existing_task_slugs.setdefault(project_id, set())
    while slug in project_slugs:
        # Check DB just in case
        row = conn.execute(
            "SELECT id FROM tasks WHERE project_id = ? AND slug = ?", (project_id, slug)).fetchone()
        if not row:
            break  # Found a gap
        slug = f"{base_slug}-{counter}"
        counter += 1
    project_slugs.add(slug)  # Add the newly assigned slug
    return slug

# --- End Migration Helper Functions ---


def init_db(db_path: str = ".pm/pm.db") -> sqlite3.Connection:
    """Initialize the database and return a connection."""
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraint enforcement
    conn.execute("PRAGMA foreign_keys = ON;")

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
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            slug TEXT NOT NULL UNIQUE, -- Add unique slug column
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            CHECK (status IN ('ACTIVE', 'PROSPECTIVE', 'COMPLETED', 'ARCHIVED', 'CANCELLED'))
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'NOT_STARTED',
            slug TEXT NOT NULL, -- Add slug column
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
            UNIQUE (project_id, slug), -- Add unique constraint for slug within project
            CHECK (status IN ('NOT_STARTED', 'IN_PROGRESS', 'BLOCKED', 'PAUSED', 'COMPLETED', 'ABANDONED'))
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

        # --- Slug Column Migration ---
        cursor = conn.execute("PRAGMA table_info(projects);")
        project_columns = {row['name'] for row in cursor.fetchall()}
        project_slug_exists = 'slug' in project_columns

        cursor = conn.execute("PRAGMA table_info(tasks);")
        task_columns = {row['name'] for row in cursor.fetchall()}
        task_slug_exists = 'slug' in task_columns

        needs_project_slug_population = False
        if not project_slug_exists:
            print("INFO: Adding 'slug' column to 'projects' table.", file=sys.stderr)
            # Add column without UNIQUE constraint first to allow population
            conn.execute("ALTER TABLE projects ADD COLUMN slug TEXT;")
            needs_project_slug_population = True

        needs_task_slug_population = False
        if not task_slug_exists:
            print("INFO: Adding 'slug' column to 'tasks' table.", file=sys.stderr)
            conn.execute("ALTER TABLE tasks ADD COLUMN slug TEXT;")
            needs_task_slug_population = True

        # Populate slugs if columns were just added
        if needs_project_slug_population:
            print("INFO: Populating slugs for existing projects...", file=sys.stderr)
            projects_to_update = conn.execute(
                "SELECT id, name FROM projects WHERE slug IS NULL;").fetchall()
            migrated_project_slugs = set()  # Track slugs assigned in this run
            # Pre-populate with any slugs that might already exist somehow (belt and suspenders)
            for row in conn.execute("SELECT slug FROM projects WHERE slug IS NOT NULL;"):
                migrated_project_slugs.add(row['slug'])

            updates = []
            for row in projects_to_update:
                base_slug = _migrate_generate_slug(row['name'])
                unique_slug = _migrate_find_unique_project_slug(
                    conn, base_slug, migrated_project_slugs)
                updates.append((unique_slug, row['id']))

            if updates:
                conn.executemany(
                    "UPDATE projects SET slug = ? WHERE id = ?", updates)
                print(
                    f"INFO: Populated slugs for {len(updates)} projects.", file=sys.stderr)
            else:
                print("INFO: No projects needed slug population.", file=sys.stderr)

            # Add UNIQUE constraint *after* population
            # Note: CREATE UNIQUE INDEX is generally safer for migrations than ALTER TABLE ADD CONSTRAINT
            print("INFO: Adding UNIQUE constraint to 'projects.slug'.",
                  file=sys.stderr)
            try:
                # This might fail if duplicates somehow exist despite population logic
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_slug ON projects(slug);")
            except sqlite3.IntegrityError as e:
                print(
                    f"WARNING: Could not create unique index on projects.slug. Duplicates might exist. Error: {e}", file=sys.stderr)

        if needs_task_slug_population:
            print("INFO: Populating slugs for existing tasks...", file=sys.stderr)
            tasks_to_update = conn.execute(
                "SELECT id, name, project_id FROM tasks WHERE slug IS NULL;").fetchall()
            # Track slugs assigned in this run {project_id: {slug1, slug2}}
            migrated_task_slugs: Dict[str, Set[str]] = {}
            # Pre-populate
            for row in conn.execute("SELECT project_id, slug FROM tasks WHERE slug IS NOT NULL;"):
                project_slugs = migrated_task_slugs.setdefault(
                    row['project_id'], set())
                project_slugs.add(row['slug'])

            updates = []
            for row in tasks_to_update:
                base_slug = _migrate_generate_slug(row['name'])
                unique_slug = _migrate_find_unique_task_slug(
                    conn, row['project_id'], base_slug, migrated_task_slugs)
                updates.append((unique_slug, row['id']))

            if updates:
                conn.executemany(
                    "UPDATE tasks SET slug = ? WHERE id = ?", updates)
                print(
                    f"INFO: Populated slugs for {len(updates)} tasks.", file=sys.stderr)
            else:
                print("INFO: No tasks needed slug population.", file=sys.stderr)

            # Add UNIQUE constraint *after* population
            print(
                "INFO: Adding UNIQUE constraint to 'tasks(project_id, slug)'.", file=sys.stderr)
            try:
                # This might fail if duplicates somehow exist despite population logic
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_project_slug ON tasks(project_id, slug);")
            except sqlite3.IntegrityError as e:
                print(
                    f"WARNING: Could not create unique index on tasks(project_id, slug). Duplicates might exist. Error: {e}", file=sys.stderr)

        # --- End Slug Column Migration ---

        # --- End Task Status CHECK Constraint Migration --- (Removed logic)

    return conn

# Project Management CLI for AI Assistants

A command-line tool designed specifically for AI assistants to manage projects and tasks.

## Overview

This tool provides a standardized way for AI assistants to manage projects, tasks, and dependencies through a simple CLI interface. It's designed to be used programmatically by AI assistants, with structured JSON output for easy parsing.

## Features

- **Project Management**: Create, read, update (including status: ACTIVE, COMPLETED, ARCHIVED), and delete projects
- **Task Management**: Create, read, update, and delete tasks with status tracking
- **Dependency Tracking**: Manage dependencies between tasks with circular dependency prevention
- **Structured Output**: JSON-formatted responses (default) or human-readable text (`--format text`)
- **SQLite Storage**: Lightweight, file-based database for easy deployment

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pm.git
cd pm

# Install the package in development mode
python3 -m pip install -e ".[dev]"
```

## Documentation

The PM tool comes with comprehensive documentation in the form of a man page. After installation, you can access it using:

```bash
man pm
```

For quick help on specific commands, you can also use the `--help` option:

```bash
pm --help
pm project --help
pm task --help
```

## Usage

**Global Options:**

- `--format {json|text}`: Specify the output format (default: `json`).
- `--db-path PATH`: Specify the path to the database file (default: `pm.db`).

These options should be placed _before_ the command group (e.g., `pm --format text project list`).

**Note on Identifiers:** Commands that accept `<project_id>` or `<task_id>` now also accept the auto-generated **slug** for that project or task (e.g., `my-project-name`, `my-task-name`). Using slugs is often more convenient than using the full UUID.

### Project Commands

```bash
# Create a project
pm project create --name "My Project" --description "Project description" [--status STATUS]

# List all projects
pm project list

# Show project details
pm project show <project_id_or_slug>

# Update a project
pm project update <project_id_or_slug> --name "New Name" --description "New description" [--status STATUS] # Prints reminder on status change

# Delete a project
pm project delete <project_id_or_slug> [--force] # Use --force to delete project and its tasks
```

### Task Commands

```bash
# Create a task
pm task create --project <project_id_or_slug> --name "My Task" --description "Task description" --status "NOT_STARTED"

# List tasks (optionally filtered)
pm task list
pm task list --project <project_id_or_slug>
pm task list --status "IN_PROGRESS"

# Show task details
pm task show <project_id_or_slug> <task_id_or_slug>

# Update a task
pm task update <project_id_or_slug> <task_id_or_slug> --name "New Name" --status "COMPLETED" # Prints reminder checklist to stderr on status change

# Delete a task
pm task delete <project_id_or_slug> <task_id_or_slug>
```

### Dependency Commands

```bash
# Add a dependency
pm task dependency add <project_id_or_slug> <task_id_or_slug> --depends-on <dependency_id_or_slug>

# Remove a dependency
pm task dependency remove <project_id_or_slug> <task_id_or_slug> --depends-on <dependency_id_or_slug>

# List dependencies
pm task dependency list <project_id_or_slug> <task_id_or_slug>
```

## Development

### Running Tests

```bash
python3 -m pytest
```

## Next Steps

1. **AI Metadata Integration**

   - Add support for storing AI-specific metadata with tasks
   - Track reasoning paths and decision points
   - Record confidence levels for decisions

2. **Handoff System**

   - Implement structured handoff between AI sessions
   - Track context and state between sessions
   - Provide clear transition points

3. **Storage Abstraction**

   - Create abstract storage interface
   - Support multiple backend options
   - Add remote storage capabilities

4. **Graph Capabilities**

   - Implement advanced dependency visualization
   - Add graph-based querying
   - Support complex dependency analysis

5. **Integration with Other Tools**
   - Add webhooks for notifications
   - Implement API for external access
   - Create plugins for popular AI platforms

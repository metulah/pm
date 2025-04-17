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
pip install pm-tool
```

## Documentation

For quick help on specific commands, you can use the `--help` option:

```bash
pm --help
pm project --help
pm task --help
```

## Project and Task Lifecycles

### Project Lifecycle

```mermaid
stateDiagram-v2
[*] --> PROSPECTIVE: Create
PROSPECTIVE --> ACTIVE: Start work
ACTIVE --> COMPLETED: Finish work
ACTIVE --> ARCHIVED: Archive
ACTIVE --> CANCELLED: Cancel
COMPLETED --> ARCHIVED: Archive
```

### Task Lifecycle

```mermaid
stateDiagram-v2
[*] --> NOT_STARTED: Create
NOT_STARTED --> IN_PROGRESS: Start work
IN_PROGRESS --> COMPLETED: Finish work
IN_PROGRESS --> BLOCKED: Encounter issue
BLOCKED --> IN_PROGRESS: Resolve issue
IN_PROGRESS --> PAUSED: Pause work
PAUSED --> IN_PROGRESS: Resume work
IN_PROGRESS --> ABANDONED: Abandon task
NOT_STARTED --> ABANDONED: Abandon task
```

The project and task lifecycles illustrate the typical status transitions for projects and tasks in the PM tool. Understanding these lifecycles helps users navigate the tool more effectively.

````


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
````

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

### Note Commands

```bash
# Add a note to a project or task
pm note add --project <project_id_or_slug> --content "Project note"
pm note add --project <project_id_or_slug> --task <task_id_or_slug> --content "Task note"

# List notes for a project or task
pm note list --project <project_id_or_slug>
pm note list --project <project_id_or_slug> --task <task_id_or_slug>

# Show a note
pm note show <note_id>

# Update a note
pm note update <note_id> --content "Updated content"

# Delete a note
pm note delete <note_id>
```

### Template Commands

```bash
# Create a task template
pm template create --name "My Task Template" --description "Template description"

# List templates
pm template list

# Show template details (including subtask templates)
pm template show <template_id>

# Add a subtask template
pm template add-subtask <template_id> --name "Subtask Template Name" [--description "Desc"] [--optional]

# Apply a template to a task (creates subtasks)
pm template apply <template_id> --task <task_id>

# Delete a template
pm template delete <template_id>
```

### Guideline Commands

```bash
# Show default guidelines
pm welcome

# Show default + specific built-in guidelines (e.g., coding, vcs)
pm welcome -g coding -g vcs

# Show default + guideline from a file path
pm welcome -g @path/to/my_guideline.md

# List custom guidelines saved in .pm/guidelines/
pm guideline list

# Show a specific custom guideline
pm guideline show <custom_guideline_name>

# Create/Update a custom guideline
pm guideline create <name> --content "Guideline content"
pm guideline update <name> --content "New content"

# Copy a built-in guideline to custom directory for modification
pm guideline copy <builtin_name> --new-name <custom_name>

# Delete a custom guideline
pm guideline delete <custom_guideline_name>
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

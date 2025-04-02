# Project Management CLI for AI Assistants

A command-line tool designed specifically for AI assistants to manage projects and tasks.

## Overview

This tool provides a standardized way for AI assistants to manage projects, tasks, and dependencies through a simple CLI interface. It's designed to be used programmatically by AI assistants, with structured JSON output for easy parsing.

## Features

- **Project Management**: Create, read, update, and delete projects
- **Task Management**: Create, read, update, and delete tasks with status tracking
- **Dependency Tracking**: Manage dependencies between tasks with circular dependency prevention
- **Structured Output**: JSON-formatted responses for easy parsing by AI assistants
- **SQLite Storage**: Lightweight, file-based database for easy deployment

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pm.git
cd pm

# Install the package in development mode
python3 -m pip install -e ".[dev]"
```

## Usage

### Project Commands

```bash
# Create a project
pm project create --name "My Project" --description "Project description"

# List all projects
pm project list

# Show project details
pm project show <project_id>

# Update a project
pm project update <project_id> --name "New Name" --description "New description"

# Delete a project
pm project delete <project_id>
```

### Task Commands

```bash
# Create a task
pm task create --project <project_id> --name "My Task" --description "Task description" --status "NOT_STARTED"

# List tasks (optionally filtered)
pm task list
pm task list --project <project_id>
pm task list --status "IN_PROGRESS"

# Show task details
pm task show <task_id>

# Update a task
pm task update <task_id> --name "New Name" --status "COMPLETED"

# Delete a task
pm task delete <task_id>
```

### Dependency Commands

```bash
# Add a dependency
pm task dependency add <task_id> --depends-on <dependency_id>

# Remove a dependency
pm task dependency remove <task_id> --depends-on <dependency_id>

# List dependencies
pm task dependency list <task_id>
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

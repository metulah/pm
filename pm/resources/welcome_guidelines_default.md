# Welcome to the PM Tool!

This tool helps manage your projects and tasks effectively through its CLI interface.

## Core Commands

- `python3 -m pm.cli project list`: List all projects
- `python3 -m pm.cli task list --project <PROJECT_ID_OR_SLUG>`: List tasks for a specific project
- `python3 -m pm.cli note list --project <PROJECT_ID_OR_SLUG> [--task <TASK_ID_OR_SLUG>]`: List notes for a project or task
- `python3 -m pm.cli project show <PROJECT_ID_OR_SLUG>`: Show project details
- `python3 -m pm.cli task show <PROJECT_ID_OR_SLUG> <TASK_ID_OR_SLUG>`: Show task details
- `python3 -m pm.cli note add --content "<CONTENT>" (--project <PROJ_ID> | --task <TASK_ID> --project <PROJ_ID>)`: Add a new note
- `python3 -m pm.cli note show <NOTE_ID>`: Show note details
- `python3 -m pm.cli note update <NOTE_ID> --content "<NEW_CONTENT>"`: Update existing note
- Use `--help` on any command (e.g., `pm task --help`, `pm task list --help`) for more options.

## Session Workflow

### Session Start

1.  Examine current state:
    - `python3 -m pm.cli project list` # Review projects
    - `python3 -m pm.cli task list --project <PROJECT_ID_OR_SLUG>` # Review tasks for a project
    - `python3 -m pm.cli note list --project <PROJECT_ID_OR_SLUG>` # Review recent project notes
2.  Review the latest notes for context.
3.  Confirm understanding of current objectives and constraints.
4.  **Set the task status to `IN_PROGRESS`**: Use `python3 -m pm.cli task update <PROJECT_ID_OR_SLUG> <TASK_ID_OR_SLUG> --status IN_PROGRESS` before starting work.

### During Session

1.  Stay focused on the current task's scope.
2.  Document significant decisions, progress, or findings using the note system:
    - `python3 -m pm.cli note add --content "<CONTENT>" --project <PROJECT_ID_OR_SLUG> --task <TASK_ID_OR_SLUG>`
3.  Before implementing, verify plan assumptions against project state/notes/relevant artifacts.
4.  Use the PM tool to track progress and state changes (e.g., updating task status if needed).
5.  Re-evaluate the plan if significant unexpected issues or new insights emerge.

### Session End (CRITICAL)

1.  Create a session handoff note **attached to the specific task worked on**:
    - `python3 -m pm.cli note add --content "<SUMMARY>" --project <PROJECT_ID_OR_SLUG> --task <TASK_ID_OR_SLUG>`
    - Include: Summary of work completed, current state, any blockers, next steps.
2.  Update task status using the PM tool (e.g., `COMPLETED`, `BLOCKED`).
    - `python3 -m pm.cli task update <PROJECT_ID_OR_SLUG> <TASK_ID_OR_SLUG> --status <NEW_STATUS>`

## Best Practices

1.  Use the PM tool for all project/task/note management.
2.  Keep task metadata (status, description) current.
3.  Add notes for significant decisions or context.
4.  Regularly verify project/task state.

## Troubleshooting

1.  Check permissions if unable to update.
2.  Verify working directory when running commands.
3.  Review latest notes if unsure of state.
4.  Ensure the tool is up to date (`pip install --upgrade .` or similar).

---

Remember to use `<COMMAND> --help` for detailed options!

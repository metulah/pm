# Welcome to the PM Tool!

This tool helps manage your projects and tasks effectively through its CLI interface.

## Core Commands

- `python3 -m pm.cli project list`: List all projects
- `python3 -m pm.cli task list`: List tasks for current project
- `python3 -m pm.cli note list`: List notes for current task/project
- `python3 -m pm.cli project show`: Show current project details
- `python3 -m pm.cli task show`: Show current task details
- `python3 -m pm.cli note add`: Add a new note
- `python3 -m pm.cli note show`: Show note details
- `python3 -m pm.cli note update`: Update existing note
- Use `--help` on any command (e.g., `pm task --help`, `pm task list --help`) for more options.

## Session Workflow

### Session Start

1.  Examine current state:
    - `python3 -m pm.cli project list` # Review projects
    - `python3 -m pm.cli task list` # Review tasks
    - `python3 -m pm.cli note list` # Review recent notes/handoffs
2.  Review the latest notes for context.
3.  Confirm understanding of current objectives and constraints.
4.  **Set the task status to `IN_PROGRESS`**: Use `python3 -m pm.cli task update <TASK_ID_OR_SLUG> --status IN_PROGRESS` before starting work.

### During Session

1.  Stay focused on the current task's scope.
2.  Document significant decisions, progress, or findings using the note system:
    - `python3 -m pm.cli note add` (Use `--task <TASK_ID_OR_SLUG>` to link to a specific task)
3.  Before implementing, verify plan assumptions against project state/notes/relevant artifacts.
4.  Use the PM tool to track progress and state changes (e.g., updating task status if needed).
5.  Re-evaluate the plan if significant unexpected issues or new insights emerge.

### Session End (CRITICAL)

1.  Create a session handoff note **attached to the specific task worked on**:
    - `python3 -m pm.cli note add --task <TASK_ID_OR_SLUG>`
    - Include: Summary of work completed, current state, any blockers, next steps.
2.  Update task status using the PM tool (e.g., `DONE`, `BLOCKED`).
    - `python3 -m pm.cli task update <TASK_ID_OR_SLUG> --status <NEW_STATUS>`

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

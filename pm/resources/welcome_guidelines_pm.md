---
description: "General usage guidelines, core commands, and session workflow for the PM tool."
---

# Welcome to the PM Tool!

This tool helps manage your projects and tasks effectively through its CLI interface.

## Core Commands

This section highlights common commands for viewing and adding information.

### Project Commands

- `pm project list`: List all projects
- `pm project show <PROJECT_ID_OR_SLUG>`: Show project details

### Task Commands

- `pm task list --project <PROJECT_ID_OR_SLUG>`: List tasks for a specific project
- `pm task show <PROJECT_ID_OR_SLUG> <TASK_ID_OR_SLUG>`: Show task details

### Note Commands

- `pm note list --project <PROJECT_ID_OR_SLUG> [--task <TASK_ID_OR_SLUG>]`: List notes for a project or task
- `pm note add --content "<CONTENT>" (--project <PROJ_ID> | --task <TASK_ID> --project <PROJ_ID>)`: Add a new note
- `pm note show <NOTE_ID>`: Show note details
- `pm note update <NOTE_ID> --content "<NEW_CONTENT>"`: Update an existing note

---

- **For other operations** (like creating, updating, or deleting projects/tasks) and more options, use `--help` on any command (e.g., `pm project --help`, `pm task create --help`).

## Session Workflow

### Session Start

1.  **Identify Target Project:**
    - List projects (consider filtering if needed): `pm project list`
    - Show details for the chosen project: `pm project show <PROJECT_ID_OR_SLUG>`
2.  **Identify Target Task(s):**
    - List tasks for the project: `pm task list --project <PROJECT_ID_OR_SLUG>` (or `pm project tasks <PROJECT_ID_OR_SLUG>`)
    - Show details for the specific task(s) you'll be working on: `pm task show <PROJECT_ID_OR_SLUG> <TASK_ID_OR_SLUG>`
3.  **Review Context (Notes):**
    - List recent notes for the project: `pm note list --project <PROJECT_ID_OR_SLUG>`
    - _Optionally_, list notes specifically for the target task: `pm note list --project <PROJECT_ID_OR_SLUG> --task <TASK_ID_OR_SLUG>`
    - Review the latest relevant notes to understand history, decisions, and blockers.
4.  **Confirm Objectives & Plan:** Ensure you understand the current goals and constraints. _Optionally, record your initial plan as a note:_ `pm note add --content "Initial plan: ..." --project <PROJECT_ID_OR_SLUG> --task <TASK_ID_OR_SLUG>`
5.  **Begin Work:** Set the task status to `IN_PROGRESS`: `pm task update <PROJECT_ID_OR_SLUG> <TASK_ID_OR_SLUG> --status IN_PROGRESS`

### During Session

1.  **Maintain Focus:** Concentrate on the objectives and scope defined for the current task.
2.  **Document Continuously:** As you make progress or decisions, record them as notes attached to the task:
    - `pm note add --content "<FINDING/DECISION/PROGRESS>" --project <PROJECT_ID_OR_SLUG> --task <TASK_ID_OR_SLUG>`
3.  **Verify Before Implementing:** Before making changes (e.g., code edits, configuration updates), double-check assumptions against the current project state, notes, or other relevant artifacts.
4.  **Track State Changes:** Update the task status promptly if circumstances change using the `pm` tool:
    - Example (Task Blocked): `pm task update <PROJECT_ID_OR_SLUG> <TASK_ID_OR_SLUG> --status BLOCKED`
    - Example (Task Paused): `pm task update <PROJECT_ID_OR_SLUG> <TASK_ID_OR_SLUG> --status PAUSED`
5.  **Adapt as Needed:** If significant unexpected issues arise or new information requires a change in direction, pause and re-evaluate the plan. Document the change in approach with a note.

### Session End (CRITICAL)

1.  Create a session handoff note **attached to the specific task worked on**:
    - `pm note add --content "<SUMMARY>" --project <PROJECT_ID_OR_SLUG> --task <TASK_ID_OR_SLUG>`
    - Include: Summary of work completed, current state, any blockers, next steps.
2.  Update task status using the PM tool (e.g., `COMPLETED`, `BLOCKED`).
    - `pm task update <PROJECT_ID_OR_SLUG> <TASK_ID_OR_SLUG> --status <NEW_STATUS>`

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

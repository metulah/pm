# Development Guidelines for PM Tool

## Project Structure

The PM tool manages projects and tasks through its CLI interface, replacing the need for manual file management. While some projects may still maintain additional documentation in their repositories, the primary project management should be done through the tool.

### Core Commands

```bash
python3 -m pm.cli project list    # List all projects
python3 -m pm.cli task list       # List tasks for current project
python3 -m pm.cli note list       # List notes for current task/project
```

## Session Management

### Session Start Requirements

1. Use the PM tool to examine current state:
   ```bash
   python3 -m pm.cli project list  # Review projects
   python3 -m pm.cli task list     # Review tasks
   python3 -m pm.cli note list     # Review recent notes/handoffs
   ```
2. Review the latest notes for context
3. Confirm understanding of current objectives and constraints
4. **Set the task status to `IN_PROGRESS`**: Use `python3 -m pm.cli task update <TASK_ID> --status IN_PROGRESS` before starting work.

### During Session Guidelines

1. Stay focused on the current task's scope
2. Before implementing a plan, verify its assumptions against the relevant codebase sections.
3. Document significant decisions using the note system:
   ```bash
   python3 -m pm.cli note add     # Add important decisions/progress
   ```
4. Use the PM tool to track progress and state changes
5. If scope changes are needed, they must be explicitly discussed with the user
6. Re-evaluate the plan if significant unexpected issues or new insights emerge during the session.

### Session End Requirements (CRITICAL)

1. Create a session handoff note **attached to the specific task worked on** using the PM tool:
   ```bash
   python3 -m pm.cli note add --task <TASK_ID> # Add session handoff note to task
   ```
   Include in the note:
   - Summary of work completed
   - Current state of the task
   - Any blockers or issues encountered
   - Next steps or recommendations
2. Commit all code changes to git with a descriptive message
3. Verify all new files are properly tracked
4. Update task status using the PM tool
5. Confirm all documentation is current and accurate

## Quality Standards

### Implementation Requirements

1. All code changes must be tested
2. Follow project's coding standards
3. No scope changes without explicit user approval
4. Document decisions and assumptions using the note system
5. Use the `--force` flag convention for destructive operations (e.g., `delete`) to prevent accidental data loss. The command should fail if `--force` is omitted.

### Testing Requirements

1. Write tests for new functionality
2. Update existing tests as needed
3. Verify all tests pass before completing task
4. Document test coverage and gaps using notes
5. Prefer creating **new, focused test files** (e.g., `test_cli_<feature>.py`) for distinct features or command groups rather than excessively expanding existing files.
6. Keep tests focused on their layer (e.g., storage tests in `test_<storage_module>.py`, CLI tests in `test_cli_<command_group>.py`).
7. **Review existing test files** (e.g., `tests/test_cli_*.py`, `tests/test_storage_*.py`) to understand established patterns (like fixture usage, test data setup, assertion styles) and conform to them where appropriate. This promotes consistency and leverages prior experience embedded in the codebase.

### Documentation Requirements

1. Use the PM tool's note system for all documentation
2. Include clear explanations of changes
3. Document any new commands or features
4. Provide examples for complex changes

## Tool Usage

### Common Commands

```bash
# Project Management
python3 -m pm.cli project list           # List all projects
python3 -m pm.cli project show           # Show current project details

# Task Management
python3 -m pm.cli task list             # List tasks for current project
python3 -m pm.cli task show             # Show current task details

# Note Management (for Documentation/Handoffs)
python3 -m pm.cli note add              # Add a new note
python3 -m pm.cli note list             # List notes for current task/project
python3 -m pm.cli note show             # Show note details
python3 -m pm.cli note update           # Update existing note
```

### Best Practices

1. Use the PM tool for all project/task/note management
2. Keep task metadata current
3. Add notes for significant decisions
4. Regularly verify project/task state

### Troubleshooting

1. Check permissions if unable to update
2. Verify working directory when running commands
3. Review latest notes if unsure of state
4. Ensure the tool is up to date
5. If database errors occur after code changes (especially related to constraints like `CHECK` or `FOREIGN KEY`), consider if a schema migration might be needed.

## Verification Checklist

Before completing any session, verify:

- [ ] Session handoff note created using PM tool
- [ ] All changes committed to git
- [ ] Tests written and passing
- [ ] Task status updated in PM tool
- [ ] No unaddressed scope changes

## Database Schema Changes

1.  **Caution:** Exercise caution when modifying the database schema (`pm/storage/db.py`). Changes can be hard to revert and may affect existing data.
2.  **Backups:** Before attempting any schema migration or potentially destructive schema change, ensure a reliable **backup strategy** is in place or that the current data is expendable.
3.  **Migrations:** SQLite has limited support for altering existing constraints. Migrations often involve renaming the old table, creating a new table with the correct schema, copying data, and dropping the old table. Plan these steps carefully.

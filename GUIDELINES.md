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

### During Session Guidelines

1. Stay focused on the current task's scope
2. Before implementing a plan, verify its assumptions against the relevant codebase sections.
3. Document significant decisions using the note system:
   ```bash
   python3 -m pm.cli note add     # Add important decisions/progress
   ```
4. Use the PM tool to track progress and state changes
5. If scope changes are needed, they must be explicitly discussed with the user

### Session End Requirements (CRITICAL)

1. Create a session handoff note using the PM tool:
   ```bash
   python3 -m pm.cli note add     # Add session handoff note
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

### Testing Requirements

1. Write tests for new functionality
2. Update existing tests as needed
3. Verify all tests pass before completing task
4. Document test coverage and gaps using notes

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

## Verification Checklist

Before completing any session, verify:

- [ ] Session handoff note created using PM tool
- [ ] All changes committed to git
- [ ] Tests written and passing
- [ ] Task status updated in PM tool
- [ ] No unaddressed scope changes

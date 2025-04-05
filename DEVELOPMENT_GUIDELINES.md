# PM Tool Development Guidelines

This document outlines specific conventions and practices for developing the PM tool itself. These supplement any general guidelines provided by the `pm welcome` command.

## Implementation Conventions

- **Destructive Operations:** Commands that perform irreversible actions (like deletion) MUST include a `--force` flag. The command should fail with an informative error message if the flag is omitted.
- **CLI Output Rendering:** Use the `rich` library (`rich.console.Console` and `rich.markdown.Markdown`) to render Markdown content (like guidelines or formatted messages) in the terminal for improved readability.

## Testing Conventions

- **Test Coverage:** While aiming for high coverage, prioritize testing critical paths and core functionality. Document significant coverage gaps using project notes if necessary.
- **File Structure:** Prefer creating new, focused test files (e.g., `test_cli_<feature>.py`, `test_storage_<module>.py`) for distinct features or command groups rather than excessively expanding existing files.
- **Test Focus:** Keep tests focused on their layer (e.g., storage tests in `test_storage_*.py`, CLI tests in `test_cli_*.py`). Avoid excessive mocking across layers where integration tests (`test_cli_integration.py`, `test_cli_workflows.py`) are more appropriate.
- **Consistency:** Review existing test files (e.g., `tests/test_cli_*.py`, `tests/test_storage_*.py`) to understand established patterns (like fixture usage, test data setup, assertion styles) and conform to them where appropriate.

## Database Changes

- **Caution:** Exercise extreme caution when modifying the database schema (`pm/storage/db.py`). Changes can be hard to revert and may affect existing data.
- **Backups:** Before attempting any schema migration or potentially destructive schema change, ensure a reliable backup strategy is in place or that the current data is expendable.
- **Migrations:** SQLite has limited support for altering existing constraints. Migrations often involve renaming the old table, creating a new table with the correct schema, copying data, and dropping the old table. Plan these steps carefully. Document migrations clearly.
- **Troubleshooting:** If database errors occur after code changes (especially related to constraints like `CHECK` or `FOREIGN KEY`), consider if a schema migration might be needed. Check for constraint violations carefully.

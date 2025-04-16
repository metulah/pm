---
metadata:
  description: Guideline on Content Detail and File Input
---

When creating or updating projects, tasks, or notes, provide detailed and comprehensive information.

**CRITICAL:** For any content (especially notes) that spans **more than two lines**, you **MUST** use a temporary file.

**Workflow:**

1.  Write the full, detailed content into a temporary file (e.g., `temp_note_content.md`).
2.  Use the `--content @<filepath>` option with the `pm` command (e.g., `pm note add --content @temp_note_content.md ...`).
3.  Delete the temporary file immediately after the `pm` command succeeds.

This ensures clarity, avoids command-line length issues, and maintains a clean history. Passing multi-line content directly inline with `--content "..."` is **STRONGLY DISCOURAGED** and should only be used for very short, single-line entries.

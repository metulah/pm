---
metadata:
  description: How to view, create, and update project guidelines using the pm tool,
    including the role of AI assistants
---

# Managing Project Guidelines

This project uses the `pm` tool to manage guidelines displayed via `pm welcome`. These guidelines ensure consistency and capture best practices. Both human operators and AI assistants play a role in maintaining their relevance.

## Viewing Guidelines

- **List all:** `pm guideline list`
- **Show specific:** `pm guideline show <guideline_name>` (e.g., `pm guideline show coding`)

## Modifying Guidelines (Collaboration Recommended)

Guidelines are stored as markdown files in the `.pm/guidelines/` directory within the project.

- **Creating New Custom Guidelines:**

  1.  Write the guideline content in a markdown file (e.g., `my_new_guideline.md`).
  2.  Use the command:
      `pm guideline create <name> --description "<description>" --content @<path_to_markdown_file>`
      (e.g., `pm guideline create my-new-rule --description "A new rule" --content @my_new_guideline.md`)
  3.  Verify with `pm guideline show <name>`.
  4.  Commit the new file created in `.pm/guidelines/`.

- **Updating Existing Custom Guidelines:**

  1.  Directly edit the corresponding markdown file in `.pm/guidelines/`.
  2.  Verify the changes using `pm guideline show <name>`.
  3.  Commit the modified file.
      _Note: Built-in guidelines cannot be modified directly._

- **Deleting Custom Guidelines:**
  _Use with caution!_
  `pm guideline delete <name>`

## Role of AI Assistants in Guideline Maintenance

- **Awareness:** AI assistants working on this project should be aware of and adhere to the established guidelines (as presented by `pm welcome`).
- **Identification:** Assistants are encouraged to **identify potential issues** with the guidelines, such as:
  - Outdated information.
  - Lack of clarity.
  - Missing guidance for recurring situations or new practices.
  - Conflicts between guidelines.
- **Collaboration:** If an assistant identifies a potential need for guideline modification, it should **propose the change** to the human operator for discussion and confirmation before attempting to create or modify guideline files using the `pm` commands. The goal is collaborative maintenance.

**Keeping guidelines up-to-date is a shared responsibility that helps ensure smooth and effective collaboration.**
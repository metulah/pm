# Ideas for `pm init` Wizard Feature

This document outlines brainstormed ideas for a new `pm init` command designed to improve the onboarding experience for new projects managed by the `pm` tool.

## Core Goal

Provide an interactive and non-interactive way to initialize a new project workspace, setting up both the `pm` tool's project entry and potentially common boilerplate files and starter tasks.

## Command Signature

`pm init [PROJECT_NAME] [OPTIONS]`

## Interactive Mode (Default Behavior - `pm init`)

- **Guidance:** Walks the user step-by-step.
- **Project Name:** Prompts if `PROJECT_NAME` argument is not provided. Suggests using the current directory name as a default.
- **Project Description:** Prompts for a description.
- **Git Initialization:** Asks "Initialize a new Git repository here? (y/N)". Runs `git init` if yes.
- **`.gitignore`:** Asks "Create a default Python .gitignore file? (y/N)". Creates the file if yes. (Consider options for other languages later).
- **`README.md`:** Asks "Create a basic README.md file? (y/N)". Creates a minimal README if yes.
- **Starter Tasks:**
  - Presents a list of suggested starter tasks (e.g., "Define project scope", "Set up development environment", "Initial commit").
  - Asks the user which, if any, they want to create within the `pm` project.
- **Confirmation:** Shows a summary of the selected actions (PM project creation, git init, file creation, task creation) and asks for confirmation before proceeding.
- **Execution:** Performs the confirmed actions.

## Non-Interactive Mode

- **`pm init <project_name>`:** Initializes with the given name. Might use default answers for other prompts or prompt minimally (e.g., only for description).
- **`pm init --defaults` / `pm init -y`:** Skips all prompts. Uses sensible defaults:
  - Project name: Current directory name.
  - Description: Empty or generic.
  - Git init: No.
  - `.gitignore`: No.
  - `README.md`: No.
  - Starter tasks: No.

## Template Support (Future Enhancement?)

- **`pm init --template <template_name>`:** Applies a predefined project template. This would likely require enhancing the existing `pm template` system to support project-level templates, potentially including directory structures, boilerplate files, and predefined task lists.

## Other Considerations

- **Directory Context:** Assumed to operate within the current working directory.
- **Error Handling:** Needs to gracefully handle cases where:
  - A `pm.db` already exists and contains a project with the same name/slug.
  - `git init` fails (e.g., already a git repo).
  - File creation fails (e.g., permissions).
- **Extensibility:** Design the interactive flow and option handling to be easily extended later.

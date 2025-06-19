---
metadata:
  description: Instructions for cutting a new release.
---

# Release Process

This document outlines the procedure for cutting a new release of the `pm-tool`. The process is automated via a GitHub Actions workflow that triggers on a git tag.

## Steps

1.  **Update Version:**

    - Modify the `version` field in the [`pyproject.toml`](./pyproject.toml:3) file to the new version number (e.g., `0.3.0`).

2.  **Run Local Checks:**

    - Execute `make check` to run all linters and tests. Ensure all checks pass before proceeding.

3.  **Commit Changes:**

    - Commit the version update to version control with a descriptive message (e.g., `Bump version to 0.3.0`).

4.  **Create Git Tag:**

    - Create a new git tag that matches the version number, prefixed with `v`.
    - Example: `git tag v0.3.0`

5.  **Push Tag to Remote:**
    - Push the new tag to the remote repository.
    - Example: `git push origin v0.3.0`

Pushing the tag will automatically trigger the `publish.yml` workflow, which builds and publishes the package to PyPI and Docker Hub.
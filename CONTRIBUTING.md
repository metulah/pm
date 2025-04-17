# Contributing to PM-Tool

Thank you for your interest in contributing!

## Development Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/metulah/pm.git
    cd pm
    ```
2.  Install in development mode (includes test dependencies):
    ```bash
    python3 -m pip install -e ".[dev]"
    ```

## Running Tests

```bash
python3 -m pytest
```

## Release Process (Publishing)

This project uses GitHub Actions to automate publishing to PyPI.

1.  **Ensure Changes are Merged:** Make sure all code changes for the release are merged into the `main` branch.
2.  **Update Version:** Increment the `version` number in `pyproject.toml`.
3.  **Commit Version Bump:** Commit the change to `pyproject.toml` (e.g., `git commit -m "chore: bump version to x.y.z"`).
4.  **Push Commits:** Push the commit(s) to the `main` branch on GitHub (`git push origin main`).
5.  **Create and Push Tag:** Create a Git tag matching the version in `pyproject.toml` (prefixed with `v`) and push it to GitHub:
    ```bash
    git tag vx.y.z
    git push origin vx.y.z
    ```
6.  **Monitor Workflow:** Pushing the tag triggers the `publish.yml` workflow in GitHub Actions. Monitor its progress to ensure the package is successfully built and published to PyPI and the Docker image is pushed to Docker Hub.

**Note:** Ensure you have the necessary permissions and that the `PYPI_API_TOKEN`, `DOCKERHUB_USERNAME`, and `DOCKERHUB_TOKEN` secrets are correctly configured in the repository settings for the workflow to succeed.

## Docker Image

This tool is also distributed as a multi-platform Docker image on Docker Hub.

- **Pull the latest image:**
  ```bash
  docker pull metulah/pm-tool:latest
  ```
- **Run the image:**
  ```bash
  docker run --rm -it metulah/pm-tool:latest --help
  ```
- **Pull a specific version:**
  ```bash
  docker pull metulah/pm-tool:vx.y.z
  ```

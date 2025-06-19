# Makefile for PM tool with uv

.PHONY: install-man test-man clean test lint check setup help

# Default Python version, can be overridden from the command line
PYTHON_VERSION ?= 3.13

# Default target
all: install-man

# Install man page to local man directory
install-man:
	@echo "Installing man page..."
	@mkdir -p $(HOME)/.local/share/man/man1
	@cp man/pm.1 $(HOME)/.local/share/man/man1/
	@echo "Man page installed. You can now run 'man pm' to view it."

# Test man page formatting
test-man:
	@echo "Testing man page formatting..."
	@mandoc man/pm.1 | less

# Clean up installed man page
clean:
	@echo "Removing installed man page..."
	@rm -f $(HOME)/.local/share/man/man1/pm.1
	@echo "Man page removed."

# Run all Python tests using uv
test: setup
	@echo "Running Python tests with Python $(PYTHON_VERSION)..."
	@uv run -p $(PYTHON_VERSION) pytest
	@echo "Tests completed."

# Run Ruff linter using uv
lint: setup
	@echo "Running Ruff linter with Python $(PYTHON_VERSION)..."
	@uv run -p $(PYTHON_VERSION) ruff check .
	@echo "Linting completed."

# Run linters and tests
check: lint test

# Set up development environment with uv
setup:
	@echo "Setting up development environment for Python $(PYTHON_VERSION)..."
	@uv sync -p $(PYTHON_VERSION) --extra dev
	@$(MAKE) install-man
	@echo "Development environment setup complete. Use 'uv run ...' to execute commands."

# Help target
help:
	@echo "Available targets:"
	@echo "  install-man  - Install man page to local man directory"
	@echo "  test-man     - Test man page formatting"
	@echo "  clean        - Remove installed man page"
	@echo "  test         - Run all Python tests (uv run pytest)"
	@echo "  lint         - Run Ruff linter (uv run ruff check .)"
	@echo "  check        - Run linters and tests"
	@echo "  setup        - Set up development environment with uv"
	@echo "  help         - Show this help message"
# Makefile for PM tool

.PHONY: install-man test-man clean test guidelines help

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

# Run all Python tests
test:
	@echo "Running Python tests..."
	@pytest
	@echo "Tests completed."

# Show relevant project guidelines
welcome:
	@echo "Displaying project development guidelines..."
	@pm welcome \
		-g coding \
		-g vcs \
		-g testing \
		-g development

# Help target
help:
	@echo "Available targets:"
	@echo "  install-man  - Install man page to local man directory"
	@echo "  test-man     - Test man page formatting"
	@echo "  clean        - Remove installed man page"
	@echo "  test         - Run all Python tests"
	@echo "  guidelines   - Display relevant project development guidelines"
	@echo "  help         - Show this help message"
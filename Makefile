# Makefile for PM tool

.PHONY: install-man test-man clean

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

# Help target
help:
	@echo "Available targets:"
	@echo "  install-man  - Install man page to local man directory"
	@echo "  test-man     - Test man page formatting"
	@echo "  clean        - Remove installed man page"
	@echo "  help         - Show this help message"
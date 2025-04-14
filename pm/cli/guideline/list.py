# pm/cli/guideline/list.py
import click
# Removed unused imports: frontmatter, Path, Console, utils, RESOURCES_DIR
# Import the new core function
from pm.core.guideline import get_available_guidelines


@click.command("list")  # Added command name for clarity, matching convention
def list_guidelines():
    """Lists available built-in and custom guidelines."""
    click.echo("Scanning for guidelines...")

    # Call the core function to get the list of all guidelines
    try:
        guidelines_found = get_available_guidelines()
    except Exception as e:
        # Basic error handling for the core function call
        click.echo(f"[Error] Failed to retrieve guidelines: {e}", err=True)
        # Consider adding more specific error handling or logging
        return  # Exit if core function fails

    if not guidelines_found:
        click.echo("No guidelines found.")
        return

    # Sorting is now handled within get_available_guidelines, no need to sort here

    click.echo("\nAvailable Guidelines:")
    # Use the structured data returned by the core function
    for g in guidelines_found:
        # Access keys defined in the core function's return type
        click.echo(
            f"- {g['slug']} [{g['type']}]: {g.get('description', 'No description available.')}")

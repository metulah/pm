# pm/cli/welcome.py
import click
import os
import io
from pathlib import Path

# Determine the base path to the resources directory relative to this file
# Path(__file__) -> pm/cli/welcome.py
# .parent -> pm/cli/
# .parent -> pm/
# / 'resources' -> pm/resources/
RESOURCES_DIR = Path(__file__).parent.parent / 'resources'
DEFAULT_GUIDELINE_NAME = 'default'
SEPARATOR = "\n\n<<<--- GUIDELINE SEPARATOR --->>>\n\n"  # Use a unique separator
# SEPARATOR = "\n---\n" # REMOVE incorrect redefinition


@click.command()
@click.option('-g', '--guidelines', 'guideline_sources', multiple=True,
              help='Specify guideline name or @filepath to append. Can be used multiple times.')
@click.pass_context  # Need context to exit
def welcome(ctx: click.Context, guideline_sources: tuple[str]):
    """Displays project guidelines, collating default and specified sources."""
    collated_content = []
    sources_to_process = (DEFAULT_GUIDELINE_NAME,) + guideline_sources
    explicit_source_error = False  # Flag to track errors in non-default sources

    for idx, source in enumerate(sources_to_process):
        is_default = (idx == 0 and source == DEFAULT_GUIDELINE_NAME)
        guideline_path = None
        content = None
        error_occurred = False

        try:
            if source.startswith('@'):
                # User-provided file path
                filepath_str = source[1:]
                if not filepath_str:
                    click.echo(
                        f"Warning: Empty file path provided with '@'. Skipping.", err=True)
                    error_occurred = True
                else:
                    potential_user_path = Path(filepath_str).resolve()
                    if potential_user_path.is_file():
                        guideline_path = potential_user_path
                    else:
                        click.echo(
                            f"Warning: Could not find or read guideline source '{source}' (File not found or not a file: {potential_user_path}).", err=True)
                        error_occurred = True
            else:
                # Built-in name
                potential_builtin_path = RESOURCES_DIR / \
                    f"welcome_guidelines_{source}.md"
                if potential_builtin_path.is_file():
                    guideline_path = potential_builtin_path
                else:
                    # Only warn for non-default missing built-ins
                    if not is_default:
                        click.echo(
                            f"Warning: Could not find or read guideline source '{source}' (Built-in name not found).", err=True)
                    else:
                        # Error specifically for missing default
                        click.echo(
                            f"Error: Default guideline file '{DEFAULT_GUIDELINE_NAME}' not found at expected location: {potential_builtin_path}", err=True)
                    error_occurred = True  # Mark error even for missing default

            # Read content if path was found
            if guideline_path and not error_occurred:
                with io.open(guideline_path, 'r', encoding='utf-8') as f:
                    content = f.read()

        except Exception as e:
            click.echo(
                f"Warning: Could not find or read guideline source '{source}' (Error: {e}).", err=True)
            error_occurred = True

        # Append content if successfully read
        if content is not None:
            if collated_content:  # Add separator if not the first piece of content
                # Use the defined unique separator
                collated_content.append(SEPARATOR)
            collated_content.append(content)
        elif error_occurred:
            if not is_default:  # Error occurred for an explicitly requested source
                explicit_source_error = True
            # If default failed to load (is_default and error_occurred), we've already printed an error.
            # We will prevent output later if explicit_source_error is True or if collated_content is empty.
            pass

    # Output the final collated content
    # Only output if no errors occurred for explicitly requested sources
    if not explicit_source_error and collated_content:
        click.echo("".join(collated_content))
    elif explicit_source_error:
        # Optionally add a final summary error message to stderr
        click.echo(
            "\nError: One or more specified guidelines could not be loaded. No output generated.", err=True)
        ctx.exit(1)  # Exit with non-zero status code
    # If collated_content is empty (e.g., default failed and nothing else requested), do nothing (exit code 0)
    # unless an explicit source error occurred, which is handled above.

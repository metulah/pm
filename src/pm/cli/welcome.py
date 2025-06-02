# pm/cli/welcome.py
import click

import toml
from pathlib import Path
import frontmatter

# Removed incorrect import: from pm.storage.guideline import get_guideline_by_name_or_slug
# Import from the new core location
# Import the utility function for resolving guideline paths
from .guideline.utils import _resolve_guideline_path

DEFAULT_GUIDELINE_NAME = "pm"
CUSTOM_GUIDELINES_DIR = Path(".pm") / "guidelines"
SEPARATOR = "\n\n<<<--- GUIDELINE SEPARATOR --->>>\n\n"
CONFIG_FILE_PATH = Path(".pm/config.toml")


@click.command()
@click.option(
    "-g",
    "--guidelines",
    "guideline_sources",
    multiple=True,
    help="Specify guideline name or @filepath to append. Can be used multiple times.",
)
@click.pass_context
def welcome(ctx: click.Context, guideline_sources: tuple[str]):
    """Displays project guidelines, collating default and specified sources."""
    collated_content = []
    default_sources = [DEFAULT_GUIDELINE_NAME]  # Default if config fails

    # --- Read configuration ---
    try:
        if CONFIG_FILE_PATH.is_file():
            with open(CONFIG_FILE_PATH, "r") as f:
                config_data = toml.load(f)
                # Safely get the list, default to empty list if keys are missing
                loaded_sources = config_data.get("guidelines", {}).get("active", None)
                if isinstance(loaded_sources, list):
                    # Use config sources if valid list is found
                    default_sources = loaded_sources
                elif loaded_sources is not None:
                    click.echo(
                        f"Warning: Invalid format for '[guidelines].active' in {CONFIG_FILE_PATH}. Expected a list.",
                        err=True,
                    )
                    # Keep default_sources as [DEFAULT_GUIDELINE_NAME]
                # If loaded_sources is None (key missing), keep default_sources
        # If file doesn't exist, default_sources remains [DEFAULT_GUIDELINE_NAME]
    except toml.TomlDecodeError as e:
        click.echo(
            f"Warning: Error parsing {CONFIG_FILE_PATH}: {e}. Using default guidelines.",
            err=True,
        )
        # Reset to default sources since config is invalid
        default_sources = [DEFAULT_GUIDELINE_NAME]
        # Clear any sources from the malformed config
        sources_to_process = default_sources
    except Exception as e:  # Catch other potential errors like permission issues
        click.echo(
            f"Warning: Could not read {CONFIG_FILE_PATH}: {e}. Using default guidelines.",
            err=True,
        )
        # Reset to default sources since config is invalid
        default_sources = [DEFAULT_GUIDELINE_NAME]
        # Clear any sources from the malformed config
        sources_to_process = default_sources
    # --- End Read configuration ---

    # Combine default sources from config (or fallback) with explicitly passed sources
    # Use a set to handle potential duplicates gracefully
    combined_sources = list(dict.fromkeys(default_sources + list(guideline_sources)))
    sources_to_process = combined_sources  # Rename for clarity in existing loop

    explicit_source_error = False  # Flag to track errors in non-default sources

    for idx, source in enumerate(sources_to_process):
        # Reset state for each source
        guideline_path = None
        content = None
        error_occurred = False
        # Check if it's the default guideline being processed when it's the only source expected
        is_sole_default_source = (
            len(sources_to_process) == 1
            and source == DEFAULT_GUIDELINE_NAME
            and not guideline_sources
        )

        try:
            # Determine if the source looks like a path or a name
            is_path_like = "/" in source or source.endswith(".md")
            is_explicit_at_path = source.startswith("@")

            if is_explicit_at_path:
                # --- Handle explicit @file path ---
                filepath_str = source[1:]
                if not filepath_str:
                    click.echo(
                        "Warning: Empty file path provided with '@'. Skipping.",
                        err=True,
                    )
                    error_occurred = True
                else:
                    # Resolve relative to CWD
                    potential_user_path = Path(filepath_str).resolve()
                    if potential_user_path.is_file():
                        guideline_path = potential_user_path
                    else:
                        click.echo(
                            f"Warning: Could not find or read guideline source '{source}' (File not found or not a file: {potential_user_path}).",
                            err=True,
                        )
                        error_occurred = True
            elif is_path_like:
                # --- Handle path-like string from config ---
                # Assume relative to CWD (where .pm/config.toml resides)
                potential_config_path = Path(source).resolve()
                if potential_config_path.is_file():
                    guideline_path = potential_config_path
                else:
                    # If path from config doesn't resolve, treat as error
                    click.echo(
                        f"Warning: Could not find guideline file specified in config: '{source}' (Resolved to: {potential_config_path}).",
                        err=True,
                    )
                    error_occurred = (
                        True  # Treat unresolved config path as an error for this source
                    )
            else:
                # --- Handle name (custom or built-in) ---
                # Use the utility function to find the path based on name
                # We don't need the type ('Custom'/'Built-in') here
                resolved_path, _ = _resolve_guideline_path(source)
                if resolved_path:
                    guideline_path = resolved_path
                else:
                    # Guideline name not found as custom or built-in file
                    if not is_sole_default_source:
                        # Warn if it wasn't the default expected guideline
                        click.echo(
                            f"Warning: Could not find guideline source '{source}' (Not found as built-in or custom file name).",
                            err=True,
                        )
                    else:
                        # Error specifically if the sole default guideline is missing
                        click.echo(
                            f"Error: Default guideline file '{DEFAULT_GUIDELINE_NAME}' not found.",
                            err=True,
                        )
                    error_occurred = True  # Mark error if name not resolved

            # --- Read content if path was determined ---
            if guideline_path and not error_occurred:
                # Use frontmatter to load and extract only the content
                post = frontmatter.load(guideline_path)
                content = post.content

        except Exception as e:
            # Catch any unexpected errors during processing
            click.echo(
                f"Warning: Error processing guideline source '{source}': {e}.", err=True
            )
            error_occurred = True

        # --- Append content or handle errors ---
        if content is not None:
            if collated_content:  # Add separator if not the first piece of content
                collated_content.append(SEPARATOR)
            collated_content.append(content)
        elif error_occurred:
            # Check if the error was for a source explicitly passed via -g
            is_explicit_source = source in guideline_sources
            if is_explicit_source:
                explicit_source_error = True
            # If the sole default failed (is_sole_default_source and error_occurred), we've already printed an error.
            pass  # Continue processing other sources
    # Note: The original loop body from line 55 to 93 is replaced by the logic inserted above.

    # Output the final collated content
    # Only output if no errors occurred for explicitly requested sources
    if not explicit_source_error and collated_content:
        click.echo("".join(collated_content))
    elif explicit_source_error:
        # Optionally add a final summary error message to stderr
        click.echo(
            "\nError: One or more specified guidelines could not be loaded. No output generated.",
            err=True,
        )
        ctx.exit(1)  # Exit with non-zero status code
    # If collated_content is empty (e.g., default failed and nothing else requested), do nothing (exit code 0)
    # unless an explicit source error occurred, which is handled above.

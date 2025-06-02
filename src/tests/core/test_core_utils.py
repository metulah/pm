"""Tests for core utility functions."""

import pytest
from pm.core.utils import generate_slug


@pytest.mark.parametrize(
    "input_name, expected_slug",
    [
        ("Simple Name", "simple-name"),
        # Corrected: Input has '/', which gets removed.
        ("  Leading/Trailing Spaces  ", "leadingtrailing-spaces"),
        ("Multiple   Spaces", "multiple-spaces"),
        ("With_Underscores", "with-underscores"),
        ("Hyphenated-Name", "hyphenated-name"),
        ("Special!@#$%^&*()_+Chars", "special-chars"),
        ("Numbers123", "numbers123"),
        ("Mix 123 with_Special!", "mix-123-with-special"),
        ("Consecutive---Hyphens", "consecutive-hyphens"),
        (" Leading-Hyphen", "leading-hyphen"),
        ("Trailing-Hyphen ", "trailing-hyphen"),
        # Corrected: Function correctly includes normalized 'unicode'.
        ("Unicode Ñame with áccents", "unicode-name-with-accents"),
        ("ALL CAPS", "all-caps"),
        ("", ""),  # Empty input remains empty
        # Corrected: These reduce to empty and should hit the fallback.
        ("---", "untitled"),
        ("!@#$", "untitled"),
        (" project name ", "project-name"),
        (" task name 1 ", "task-name-1"),
    ]
)
def test_generate_slug(input_name, expected_slug):
    """Test the generate_slug function with various inputs."""
    assert generate_slug(input_name) == expected_slug

# Redundant test removed as cases are covered in parameterized test above.
    assert generate_slug("---") == "untitled"

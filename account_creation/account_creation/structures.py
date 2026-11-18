"""The parking structures and lots, and the levels each one has.

Edit this one file to change them everywhere: the dropdowns on the dashboard
and the server-side validation both read from here.
"""

STRUCTURE_LEVELS = {
    "Nutwood Structure": ("1", "2", "3", "4", "5"),
    "State College Structure": ("1", "2", "3", "4", "5", "6"),
    "Eastside North": ("1", "2", "3", "4", "5", "6"),
    "Eastside South": ("1", "2", "3", "4", "5", "6"),
    # S8 and S10 are surface lots, so there is only the ground level.
    "S8 / S10": ("Ground",),
}

PARKING_STRUCTURES = tuple(STRUCTURE_LEVELS)


def is_valid_spot(structure, level):
    """True only if the structure exists and actually has that level."""
    return level in STRUCTURE_LEVELS.get(structure, ())

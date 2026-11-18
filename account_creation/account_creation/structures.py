"""The parking structures and the levels each one has.

PLACEHOLDER DATA: the level lists below are guesses. Check them against
CSUF's parking maps and edit this one file to fix them everywhere
(dropdowns and server-side validation both read from here).
"""

STRUCTURE_LEVELS = {
    "Nutwood Structure": ("1", "2", "3", "4", "5", "6", "7"),
    "State College Structure": ("1", "2", "3", "4", "5", "6", "7"),
    "Eastside North": ("1", "2", "3", "4", "5", "6"),
    "Eastside South": ("1", "2", "3", "4", "5", "6"),
    "S8 / S10": ("1", "2", "3", "Roof"),
}

PARKING_STRUCTURES = tuple(STRUCTURE_LEVELS)


def is_valid_spot(structure, level):
    """True only if the structure exists and actually has that level."""
    return level in STRUCTURE_LEVELS.get(structure, ())

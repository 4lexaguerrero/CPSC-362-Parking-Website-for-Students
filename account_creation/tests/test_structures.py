import unittest

from account_creation.account_creation.structures import (
    PARKING_STRUCTURES,
    STRUCTURE_LEVELS,
    is_valid_spot,
)


class StructureLevelTests(unittest.TestCase):
    def test_each_structure_has_the_right_number_of_levels(self):
        self.assertEqual(len(STRUCTURE_LEVELS["Nutwood Structure"]), 5)
        self.assertEqual(len(STRUCTURE_LEVELS["State College Structure"]), 6)
        self.assertEqual(len(STRUCTURE_LEVELS["Eastside North"]), 6)
        self.assertEqual(len(STRUCTURE_LEVELS["Eastside South"]), 6)

    def test_s8_and_s10_are_ground_level_only(self):
        self.assertEqual(STRUCTURE_LEVELS["S8 / S10"], ("Ground",))

    def test_every_listed_structure_has_levels(self):
        for name in PARKING_STRUCTURES:
            self.assertTrue(STRUCTURE_LEVELS[name], name)

    def test_is_valid_spot_checks_the_pair(self):
        self.assertTrue(is_valid_spot("Nutwood Structure", "5"))
        self.assertFalse(is_valid_spot("Nutwood Structure", "6"))
        self.assertTrue(is_valid_spot("Eastside South", "6"))
        self.assertTrue(is_valid_spot("S8 / S10", "Ground"))
        self.assertFalse(is_valid_spot("S8 / S10", "1"))
        self.assertFalse(is_valid_spot("Unknown", "1"))


if __name__ == "__main__":
    unittest.main()

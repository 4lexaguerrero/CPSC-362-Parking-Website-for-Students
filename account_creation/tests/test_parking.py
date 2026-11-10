import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from account_creation.account_creation.parking import SQLiteParkingRepository


class SQLiteParkingRepositoryTests(unittest.TestCase):
    def test_parking_history_persists_and_new_entry_closes_previous_one(self):
        with TemporaryDirectory() as directory:
            database_path = str(Path(directory) / "parking.db")
            repository = SQLiteParkingRepository(database_path)

            first = repository.log_parking(
                7, "Nutwood Structure", "2", "2026-11-08T10:00:00+00:00"
            )
            self.assertEqual(first["structure"], "Nutwood Structure")
            self.assertIsNone(first["left_at"])

            second = repository.log_parking(
                7, "Eastside North", "3", "2026-11-08T11:00:00+00:00"
            )
            self.assertEqual(second["structure"], "Eastside North")

            reopened_repository = SQLiteParkingRepository(database_path)
            history = reopened_repository.get_recent(7)
            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["structure"], "Eastside North")
            self.assertEqual(history[1]["left_at"], "2026-11-08T11:00:00+00:00")
            self.assertEqual(reopened_repository.get_active(7)["log_id"], second["log_id"])

    def test_mark_left_only_changes_the_current_users_active_entry(self):
        with TemporaryDirectory() as directory:
            repository = SQLiteParkingRepository(str(Path(directory) / "parking.db"))
            repository.log_parking(7, "Nutwood Structure", "2")
            repository.log_parking(8, "Eastside North", "1")

            self.assertTrue(repository.mark_left(7, "2026-11-08T12:00:00+00:00"))
            self.assertIsNone(repository.get_active(7))
            self.assertIsNotNone(repository.get_active(8))
            self.assertFalse(repository.mark_left(7))


if __name__ == "__main__":
    unittest.main()
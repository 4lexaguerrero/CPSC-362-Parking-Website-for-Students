import sqlite3
import time
from contextlib import closing

STRUCTURES = [
    "Nutwood Structure",
    "State College Structure",
    "Eastside North",
    "Eastside South",
    "S8 / S10",
]
LEVELS = ["1", "2", "3", "4", "5", "6", "7", "Roof"]


class ParkingLogRepository:
    """Stores where students say they parked. Lives in the same SQLite file as users."""

    def __init__(self, db_path="parking_accounts.db"):
        self.db_path = db_path
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS parking_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    structure TEXT NOT NULL,
                    level TEXT NOT NULL,
                    parked_at REAL NOT NULL,
                    left_at REAL
                )
                """
            )
            connection.commit()

    def log_parking(self, user_id, structure, level):
        if structure not in STRUCTURES:
            raise ValueError("Please choose a parking structure.")
        if level not in LEVELS:
            raise ValueError("Please choose a level.")

        now = time.time()
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                # A student can only be parked in one place at a time.
                connection.execute(
                    "UPDATE parking_logs SET left_at = ? "
                    "WHERE user_id = ? AND left_at IS NULL",
                    (now, user_id),
                )
                connection.execute(
                    "INSERT INTO parking_logs (user_id, structure, level, parked_at) "
                    "VALUES (?, ?, ?, ?)",
                    (user_id, structure, level, now),
                )

    def mark_left(self, user_id):
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                connection.execute(
                    "UPDATE parking_logs SET left_at = ? "
                    "WHERE user_id = ? AND left_at IS NULL",
                    (time.time(), user_id),
                )

    def get_active(self, user_id):
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute(
                "SELECT log_id, structure, level, parked_at, left_at FROM parking_logs "
                "WHERE user_id = ? AND left_at IS NULL "
                "ORDER BY parked_at DESC LIMIT 1",
                (user_id,),
            ).fetchone()
        return self._row_to_log(row)

    def get_recent(self, user_id, limit=5):
        with closing(sqlite3.connect(self.db_path)) as connection:
            rows = connection.execute(
                "SELECT log_id, structure, level, parked_at, left_at FROM parking_logs "
                "WHERE user_id = ? ORDER BY parked_at DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [self._row_to_log(row) for row in rows]

    def active_counts(self):
        """How many students currently report being parked in each structure."""
        counts = {name: 0 for name in STRUCTURES}
        with closing(sqlite3.connect(self.db_path)) as connection:
            rows = connection.execute(
                "SELECT structure, COUNT(*) FROM parking_logs "
                "WHERE left_at IS NULL GROUP BY structure"
            ).fetchall()
        for structure, count in rows:
            if structure in counts:
                counts[structure] = count
        return counts

    @staticmethod
    def _row_to_log(row):
        if row is None:
            return None
        return {
            "log_id": row[0],
            "structure": row[1],
            "level": row[2],
            "parked_at": row[3],
            "left_at": row[4],
        }

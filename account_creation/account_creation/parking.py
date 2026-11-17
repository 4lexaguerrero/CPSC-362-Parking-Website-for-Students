import sqlite3
from contextlib import closing
from datetime import datetime, timezone


class SQLiteParkingRepository:
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
                    parked_at TEXT NOT NULL,
                    left_at TEXT
                )
                """
            )
            connection.commit()

    def log_parking(self, user_id, structure, level, parked_at=None):
        parked_at = parked_at or self._now()
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                connection.execute(
                    """
                    UPDATE parking_logs SET left_at = ?
                    WHERE user_id = ? AND left_at IS NULL
                    """,
                    (parked_at, user_id),
                )
                cursor = connection.execute(
                    """
                    INSERT INTO parking_logs (user_id, structure, level, parked_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, structure, str(level), parked_at),
                )
        return self.get_active(user_id)

    def mark_left(self, user_id, left_at=None):
        left_at = left_at or self._now()
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE parking_logs SET left_at = ?
                    WHERE log_id = (
                        SELECT log_id FROM parking_logs
                        WHERE user_id = ? AND left_at IS NULL
                        ORDER BY log_id DESC LIMIT 1
                    )
                    """,
                    (left_at, user_id),
                )
        return cursor.rowcount == 1

    def get_active(self, user_id):
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute(
                """
                SELECT log_id, structure, level, parked_at, left_at
                FROM parking_logs
                WHERE user_id = ? AND left_at IS NULL
                ORDER BY log_id DESC LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        return self._row_to_log(row)

    def get_recent(self, user_id, limit=10):
        limit = max(1, min(int(limit), 50))
        with closing(sqlite3.connect(self.db_path)) as connection:
            rows = connection.execute(
                """
                SELECT log_id, structure, level, parked_at, left_at
                FROM parking_logs WHERE user_id = ?
                ORDER BY log_id DESC LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        return [self._row_to_log(row) for row in rows]

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

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
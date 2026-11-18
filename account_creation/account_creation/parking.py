import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone


# A parking log that is never closed stops counting after this long.
MAX_PARKING_DURATION = timedelta(hours=5)


class ActiveParkingError(ValueError):
    """Raised when someone tries to log a new spot while still parked."""


class SQLiteParkingRepository:
    def __init__(self, db_path="parking_accounts.db", max_duration=MAX_PARKING_DURATION):
        self.db_path = db_path
        self.max_duration = max_duration
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
        """Log a new spot. The user must not already be parked."""
        parked_at = parked_at or self._now()
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                self._expire_stale(connection, user_id, parked_at)
                if self._select_active(connection, user_id) is not None:
                    raise ActiveParkingError(
                        "You are already parked. Mark yourself as left "
                        "before logging a new spot."
                    )
                connection.execute(
                    """
                    INSERT INTO parking_logs (user_id, structure, level, parked_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, structure, str(level), parked_at),
                )
        return self.get_active(user_id, now=parked_at)

    def mark_left(self, user_id, left_at=None):
        left_at = left_at or self._now()
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                self._expire_stale(connection, user_id, left_at)
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

    def get_active(self, user_id, now=None):
        now = now or self._now()
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                self._expire_stale(connection, user_id, now)
            return self._select_active(connection, user_id)

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

    def _select_active(self, connection, user_id):
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

    def _expire_stale(self, connection, user_id, now):
        """Close any open log older than max_duration (people forget to leave)."""
        now_time = self._parse(now)
        rows = connection.execute(
            "SELECT log_id, parked_at FROM parking_logs "
            "WHERE user_id = ? AND left_at IS NULL",
            (user_id,),
        ).fetchall()
        for log_id, parked_at in rows:
            parked_time = self._parse(parked_at)
            if now_time - parked_time >= self.max_duration:
                left_at = (parked_time + self.max_duration).isoformat(timespec="seconds")
                connection.execute(
                    "UPDATE parking_logs SET left_at = ? WHERE log_id = ?",
                    (left_at, log_id),
                )

    @staticmethod
    def _parse(value):
        moment = datetime.fromisoformat(value)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        return moment

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

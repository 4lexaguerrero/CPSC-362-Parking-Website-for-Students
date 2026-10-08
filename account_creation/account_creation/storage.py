import sqlite3
from contextlib import closing


class InMemoryUserRepository:
    def __init__(self):
        self._users = {}
        self._users_by_id = {}
        self._next_user_id = 1

    def add_user(self, account):
        email = account["email"]
        account["user_id"] = self._next_user_id
        self._next_user_id += 1
        self._users[email] = account
        self._users_by_id[account["user_id"]] = account
        return account

    def get_user_by_email(self, email):
        return self._users.get(email)

    def get_user_by_id(self, user_id):
        return self._users_by_id.get(user_id)

    def update_user(self, account):
        self._users[account["email"]] = account
        self._users_by_id[account["user_id"]] = account


class SQLiteUserRepository:
    def __init__(self, db_path="parking_accounts.db"):
        self.db_path = db_path
        with closing(sqlite3.connect(self.db_path)) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                    email_verification_required INTEGER NOT NULL DEFAULT 0,
                    verification_code_hash TEXT,
                    verification_code_expires_at REAL
                )
                """
            )
            connection.commit()

    def add_user(self, account):
        try:
            with closing(sqlite3.connect(self.db_path)) as connection:
                with connection:
                    cursor = connection.execute(
                        """
                        INSERT INTO users (
                            first_name, last_name, email, password_hash,
                            failed_login_attempts, email_verification_required,
                            verification_code_hash, verification_code_expires_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            account["first_name"],
                            account["last_name"],
                            account["email"],
                            account["password_hash"],
                            account.get("failed_login_attempts", 0),
                            int(account.get("email_verification_required", False)),
                            account.get("verification_code_hash"),
                            account.get("verification_code_expires_at"),
                        ),
                    )
                    account["user_id"] = cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise ValueError(
                f"An account with email '{account['email']}' already exists."
            ) from error

        return account

    def get_user_by_email(self, email):
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute(
                """
                SELECT user_id, first_name, last_name, email, password_hash,
                       failed_login_attempts, email_verification_required,
                       verification_code_hash, verification_code_expires_at
                FROM users WHERE email = ?
                """,
                (email,),
            ).fetchone()
        return self._row_to_user(row)

    def get_user_by_id(self, user_id):
        with closing(sqlite3.connect(self.db_path)) as connection:
            row = connection.execute(
                """
                SELECT user_id, first_name, last_name, email, password_hash,
                       failed_login_attempts, email_verification_required,
                       verification_code_hash, verification_code_expires_at
                FROM users WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
        return self._row_to_user(row)

    def update_user(self, account):
        with closing(sqlite3.connect(self.db_path)) as connection:
            with connection:
                cursor = connection.execute(
                    """
                    UPDATE users
                    SET first_name = ?, last_name = ?, email = ?, password_hash = ?,
                        failed_login_attempts = ?, email_verification_required = ?,
                        verification_code_hash = ?, verification_code_expires_at = ?
                    WHERE user_id = ?
                    """,
                    (
                        account["first_name"],
                        account["last_name"],
                        account["email"],
                        account["password_hash"],
                        account.get("failed_login_attempts", 0),
                        int(account.get("email_verification_required", False)),
                        account.get("verification_code_hash"),
                        account.get("verification_code_expires_at"),
                        account["user_id"],
                    ),
                )
                if cursor.rowcount != 1:
                    raise ValueError(f"Account {account['user_id']} does not exist.")

    @staticmethod
    def _row_to_user(row):
        if row is None:
            return None

        return {
            "user_id": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "email": row[3],
            "password_hash": row[4],
            "failed_login_attempts": row[5],
            "email_verification_required": bool(row[6]),
            "verification_code_hash": row[7],
            "verification_code_expires_at": row[8],
        }

import hashlib


class AccountService:
    def __init__(self, repository):
        self.repository = repository

    def create_account(self, first_name, last_name, email, password):
        first_name = self._clean_name(first_name, "first name")
        last_name = self._clean_name(last_name, "last name")
        email = self._clean_email(email)
        self._validate_password(password)

        if self.repository.get_user_by_email(email):
            raise ValueError(f"An account with email '{email}' already exists.")

        account = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password_hash": self._hash_password(password),
        }

        self.repository.add_user(account)
        return account

    def _clean_name(self, value, field_name):
        if value is None or value.strip() == "":
            raise ValueError(f"{field_name.title()} is required.")
        return value.strip()

    def _clean_email(self, email):
        if email is None:
            raise ValueError("Email is required.")

        email = email.strip().lower()
        if "@" not in email:
            raise ValueError("Email must include @.")

        # Keep this simple for now: accept a CSUF student email only.
        if not email.endswith("@csu.fullerton.edu"):
            raise ValueError("Email must be a CSUF student email.")

        return email

    def _validate_password(self, password):
        if password is None or len(password) < 10:
            raise ValueError("Password must be at least 10 characters long.")
        
#for hashing passwords (will work on this more) source: https://www.geeksforgeeks.org/hashing-passwords-in-python/
    @staticmethod
    def _hash_password(password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

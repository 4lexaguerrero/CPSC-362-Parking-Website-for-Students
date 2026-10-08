import hashlib
import hmac
import secrets
import time
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError


_PASSWORD_HASHER = PasswordHasher()


class AccountService:
    MAX_LOGIN_ATTEMPTS = 5
    VERIFICATION_CODE_LIFETIME_SECONDS = 600

    def __init__(self, repository, email_sender=None):
        self.repository = repository
        self.email_sender = email_sender

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

        return self.repository.add_user(account)

    def login(self, email, password):
        email = self._clean_email(email)
        account = self.repository.get_user_by_email(email)

        if account is None:
            raise ValueError("Invalid email or password.")

        if account.get("email_verification_required"):
            raise ValueError("Email verification is required before you can log in.")

        password_matches = False
        if isinstance(password, str):
            try:
                password_matches = _PASSWORD_HASHER.verify(
                    account["password_hash"], password
                )
            except VerifyMismatchError:
                pass
            except InvalidHashError:
                legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
                if hmac.compare_digest(account["password_hash"], legacy_hash):
                    account["password_hash"] = self._hash_password(password)
                    password_matches = True
            except VerificationError:
                pass

        if not password_matches:
            failed_attempts = account.get("failed_login_attempts", 0) + 1
            account["failed_login_attempts"] = failed_attempts

            if failed_attempts >= self.MAX_LOGIN_ATTEMPTS:
                account["email_verification_required"] = True
                self.repository.update_user(account)
                self._send_login_verification(account)
                raise ValueError(
                    "Too many failed login attempts. A verification code was sent by email."
                )

            self.repository.update_user(account)
            raise ValueError("Invalid email or password.")

        account["failed_login_attempts"] = 0
        self.repository.update_user(account)
        return {
            "user_id": account["user_id"],
            "first_name": account["first_name"],
            "last_name": account["last_name"],
            "email": account["email"],
        }

    def verify_login_email(self, email, verification_code):
        email = self._clean_email(email)
        account = self.repository.get_user_by_email(email)

        if account is None or not account.get("email_verification_required"):
            raise ValueError("There is no pending email verification for this account.")

        if time.time() >= account.get("verification_code_expires_at", 0):
            raise ValueError("The verification code expired. Request a new code.")

        if not isinstance(verification_code, str):
            raise ValueError("The verification code is invalid.")

        code_hash = hashlib.sha256(verification_code.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(account["verification_code_hash"], code_hash):
            raise ValueError("The verification code is invalid.")

        account["email_verification_required"] = False
        account["failed_login_attempts"] = 0
        account.pop("verification_code_hash", None)
        account.pop("verification_code_expires_at", None)
        self.repository.update_user(account)

    def resend_login_verification(self, email):
        email = self._clean_email(email)
        account = self.repository.get_user_by_email(email)

        if account is None or not account.get("email_verification_required"):
            raise ValueError("There is no pending email verification for this account.")

        self._send_login_verification(account)

    def _send_login_verification(self, account):
        if self.email_sender is None:
            raise RuntimeError("An email sender must be configured to send verification codes.")

        verification_code = str(secrets.randbelow(1_000_000)).zfill(6)
        self.email_sender(account["email"], verification_code)
        account["verification_code_hash"] = hashlib.sha256(
            verification_code.encode("utf-8")
        ).hexdigest()
        account["verification_code_expires_at"] = (
            time.time() + self.VERIFICATION_CODE_LIFETIME_SECONDS
        )
        self.repository.update_user(account)

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
        
    @staticmethod
    def _hash_password(password):
        return _PASSWORD_HASHER.hash(password)

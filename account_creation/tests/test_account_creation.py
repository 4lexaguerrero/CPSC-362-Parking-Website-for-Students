import unittest
#Unit tests for the AccountService class.

from account_creation.account_creation.accountlogic import AccountService
from account_creation.account_creation.storage import InMemoryUserRepository


class AccountServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = AccountService(InMemoryUserRepository())

    def test_create_account_success(self):
        account = self.service.create_account(
            first_name="Alexa",
            last_name="Guerrero",
            email="alexa@csu.fullerton.edu",
            password="StrongPass123!",
        )

        self.assertEqual(account["first_name"], "Alexa")
        self.assertEqual(account["email"], "alexa@csu.fullerton.edu")
        self.assertTrue(account["password_hash"])
        self.assertNotEqual(account["password_hash"], "StrongPass123!")

    def test_create_account_rejects_duplicate_email(self):
        self.service.create_account(
            first_name="Alexa",
            last_name="Guerrero",
            email="alexa@csu.fullerton.edu",
            password="StrongPass123!",
        )

        with self.assertRaises(ValueError):
            self.service.create_account(
                first_name="Jose",
                last_name="Garcia",
                email="jose@csu.fullerton.edu",
                password="AnotherPass123!",
            )

    def test_create_account_rejects_weak_password(self):
        with self.assertRaises(ValueError):
            self.service.create_account(
                first_name="Alexa",
                last_name="Guerrero",
                email="alexa@csu.fullerton.edu",
                password="short",
            )


if __name__ == "__main__":
    unittest.main()

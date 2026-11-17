import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app import create_app
from account_creation.account_creation.accountlogic import AccountService
from account_creation.account_creation.parking import SQLiteParkingRepository
from account_creation.account_creation.storage import InMemoryUserRepository


class AuthenticationRouteTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        parking = SQLiteParkingRepository(
            str(Path(self.directory.name) / "parking.db")
        )
        service = AccountService(InMemoryUserRepository())
        service.create_account(
            first_name="Alexa",
            last_name="Guerrero",
            email="alexa@csu.fullerton.edu",
            password="StrongPass123!",
        )
        self.app = create_app(service, parking)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        self.directory.cleanup()

    def test_dashboard_requires_login_and_displays_logged_in_user(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")

        response = self.client.post(
            "/login",
            data={"email": "alexa@csu.fullerton.edu", "password": "StrongPass123!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/dashboard")

        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome, Alexa", response.data)

    def test_logout_clears_session_and_protects_dashboard_again(self):
        self.client.post(
            "/login",
            data={"email": "alexa@csu.fullerton.edu", "password": "StrongPass123!"},
        )

        response = self.client.post("/logout")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")
        self.assertEqual(self.client.get("/dashboard").status_code, 302)

    def test_student_can_log_parking_mark_left_and_view_history(self):
        self.client.post(
            "/login",
            data={"email": "alexa@csu.fullerton.edu", "password": "StrongPass123!"},
        )

        response = self.client.post(
            "/dashboard/park",
            data={"structure": "Nutwood Structure", "level": "2"},
            follow_redirects=True,
        )
        self.assertIn(b"Your parking location was logged.", response.data)
        self.assertIn(b"Nutwood Structure, Level 2", response.data)
        self.assertIn(b"still parked", response.data)

        response = self.client.post("/dashboard/leave", follow_redirects=True)
        self.assertIn(b"Your parking session is marked as ended.", response.data)
        self.assertIn(b"left", response.data)

    def test_parking_routes_require_login_and_reject_invalid_choices(self):
        response = self.client.post(
            "/dashboard/park",
            data={"structure": "Unknown", "level": "99"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")

        self.client.post(
            "/login",
            data={"email": "alexa@csu.fullerton.edu", "password": "StrongPass123!"},
        )
        response = self.client.post(
            "/dashboard/park",
            data={"structure": "Unknown", "level": "99"},
            follow_redirects=True,
        )
        self.assertIn(b"Choose a valid parking structure and level.", response.data)


if __name__ == "__main__":
    unittest.main()
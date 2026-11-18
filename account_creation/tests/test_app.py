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

    def log_in(self):
        self.client.post(
            "/login",
            data={"email": "alexa@csu.fullerton.edu", "password": "StrongPass123!"},
        )

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
        self.log_in()

        response = self.client.post("/logout")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/login")
        self.assertEqual(self.client.get("/dashboard").status_code, 302)

    def test_student_can_log_parking_mark_left_and_view_history(self):
        self.log_in()

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

        self.log_in()
        response = self.client.post(
            "/dashboard/park",
            data={"structure": "Unknown", "level": "99"},
            follow_redirects=True,
        )
        self.assertIn(b"Choose a valid parking structure and level.", response.data)

    def test_level_must_exist_in_the_chosen_structure(self):
        self.log_in()

        # Nutwood has 5 levels, so level 6 is rejected.
        response = self.client.post(
            "/dashboard/park",
            data={"structure": "Nutwood Structure", "level": "6"},
            follow_redirects=True,
        )
        self.assertIn(b"Choose a valid parking structure and level.", response.data)
        self.assertNotIn(b"still parked", response.data)

        # S8 / S10 are ground-level lots, so a numbered level is rejected.
        response = self.client.post(
            "/dashboard/park",
            data={"structure": "S8 / S10", "level": "1"},
            follow_redirects=True,
        )
        self.assertIn(b"Choose a valid parking structure and level.", response.data)

        response = self.client.post(
            "/dashboard/park",
            data={"structure": "S8 / S10", "level": "Ground"},
            follow_redirects=True,
        )
        self.assertIn(b"Your parking location was logged.", response.data)
        self.assertIn(b"S8 / S10, Ground level", response.data)

    def test_dashboard_sends_each_structures_levels_to_the_page(self):
        self.log_in()
        response = self.client.get("/dashboard")
        self.assertIn(b"structureLevels", response.data)
        self.assertIn(b'"Nutwood Structure": ["1", "2", "3", "4", "5"]', response.data)
        self.assertIn(b'"S8 / S10": ["Ground"]', response.data)

    def test_cannot_log_new_spot_until_marked_as_left(self):
        self.log_in()
        self.client.post(
            "/dashboard/park",
            data={"structure": "Nutwood Structure", "level": "2"},
        )

        # The park form is hidden while a spot is active.
        response = self.client.get("/dashboard")
        self.assertNotIn(b"Log my parking", response.data)
        self.assertIn(b"I've left", response.data)

        # A direct request is rejected and the original spot is kept.
        response = self.client.post(
            "/dashboard/park",
            data={"structure": "Eastside North", "level": "3"},
            follow_redirects=True,
        )
        self.assertIn(b"Mark yourself as left", response.data)
        self.assertIn(b"Nutwood Structure, Level 2", response.data)
        self.assertNotIn(b"Eastside North, Level 3", response.data)

        # After leaving, logging a new spot works and the form returns.
        self.client.post("/dashboard/leave")
        response = self.client.get("/dashboard")
        self.assertIn(b"Log my parking", response.data)

        response = self.client.post(
            "/dashboard/park",
            data={"structure": "Eastside North", "level": "3"},
            follow_redirects=True,
        )
        self.assertIn(b"Your parking location was logged.", response.data)
        self.assertIn(b"Eastside North, Level 3", response.data)

    def test_login_shows_message_instead_of_crashing_when_email_sender_is_missing(self):
        for _ in range(5):
            response = self.client.post(
                "/login",
                data={"email": "alexa@csu.fullerton.edu", "password": "wrong-password"},
            )
        self.assertEqual(response.status_code, 429)
        self.assertIn(b"Too many failed attempts", response.data)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import os
import secrets

from flask import Flask, flash, redirect, render_template, request, session, url_for

from account_creation.account_creation.accountlogic import AccountService
from account_creation.account_creation.parking import SQLiteParkingRepository
from account_creation.account_creation.storage import SQLiteUserRepository


PROJECT_ROOT = Path(__file__).resolve().parent
PARKING_STRUCTURES = (
    "Nutwood Structure",
    "State College Structure",
    "Eastside North",
    "Eastside South",
    "S8 / S10",
)
PARKING_LEVELS = ("1", "2", "3", "4", "5")


def create_app(account_service=None, parking_repository=None):
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT),
        static_folder=str(PROJECT_ROOT / "css"),
        static_url_path="/css",
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    database_path = str(PROJECT_ROOT / "parking_accounts.db")
    service = account_service or AccountService(
        SQLiteUserRepository(database_path)
    )
    parking = parking_repository or SQLiteParkingRepository(database_path)

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        form_data = {"first_name": "", "last_name": "", "email": ""}
        if request.method == "GET":
            return render_template("signup.html", form_data=form_data)

        form_data.update(
            first_name=request.form.get("first_name", ""),
            last_name=request.form.get("last_name", ""),
            email=request.form.get("email", ""),
        )
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if password != password_confirm:
            return (
                render_template(
                    "signup.html",
                    form_data=form_data,
                    error_message="Passwords do not match.",
                ),
                400,
            )

        try:
            account = service.create_account(
                first_name=form_data["first_name"],
                last_name=form_data["last_name"],
                email=form_data["email"],
                password=password,
            )
        except ValueError as error:
            return (
                render_template(
                    "signup.html",
                    form_data=form_data,
                    error_message=str(error),
                ),
                400,
            )

        # New accounts go straight to the dashboard.
        session["user_id"] = account["user_id"]
        session["first_name"] = account["first_name"]
        flash("Account created. Welcome to Spotter!")
        return redirect(url_for("dashboard"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "")
            password = request.form.get("password", "")
            try:
                user = service.login(email, password)
            except ValueError:
                return (
                    render_template(
                        "login.html",
                        error_message="Too many failed attempts. Try again later.",
                    ),
                    401,
                )
            session.clear()
            session["user_id"] = user["user_id"]
            session["first_name"] = user["first_name"]
            return redirect(url_for("dashboard"))

        return render_template("login.html")

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("home"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        user_id = session["user_id"]
        reported = parking.active_counts()
        structures = []
        for name in STRUCTURES:
            available = OFFICIAL_COUNTS.get(name, 0)
            structures.append(
                {
                    "name": name,
                    "available": "Full" if available <= 0 else f"{available:,}",
                    "status": structure_status(available),
                    "reported": reported.get(name, 0),
                }
            )
        return render_template(
            "dashboard.html",
            first_name=session.get("first_name", ""),
            structures=structures,
            levels=LEVELS,
            active=parking.get_active(user_id),
            recent=parking.get_recent(user_id, limit=5),
            messages=get_flashed_messages(with_categories=True),
        )

    @app.get("/dashboard")
    def dashboard():
        if "user_id" not in session:
            return redirect(url_for("login"))
        user_id = session["user_id"]
        return render_template(
            "dashboard.html",
            first_name=session["first_name"],
            active=parking.get_active(user_id),
            recent=parking.get_recent(user_id),
            parking_structures=PARKING_STRUCTURES,
            levels=PARKING_LEVELS,
        )

    @app.post("/dashboard/park")
    def log_parking():
        if "user_id" not in session:
            return redirect(url_for("login"))

        structure = request.form.get("structure", "")
        level = request.form.get("level", "")
        if structure not in PARKING_STRUCTURES or level not in PARKING_LEVELS:
            flash("Choose a valid parking structure and level.", "error")
            return redirect(url_for("dashboard"))

        parking.log_parking(session["user_id"], structure, level)
        flash("Your parking location was logged.", "success")
        return redirect(url_for("dashboard"))

    @app.post("/dashboard/leave")
    def mark_left():
        if "user_id" not in session:
            return redirect(url_for("login"))

        if parking.mark_left(session["user_id"]):
            flash("Your parking session is marked as ended.", "success")
        else:
            flash("There is no active parking location to end.", "error")
        return redirect(url_for("dashboard"))

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

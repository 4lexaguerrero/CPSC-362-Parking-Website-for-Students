import os
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (
    Flask,
    flash,
    get_flashed_messages,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from account_creation.account_creation.accountlogic import AccountService
from account_creation.account_creation.parkinglog import (
    LEVELS,
    STRUCTURES,
    ParkingLogRepository,
)
from account_creation.account_creation.storage import SQLiteUserRepository


PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = str(PROJECT_ROOT / "parking_accounts.db")

# Placeholder "official" numbers until the CSUF scraper is hooked in.
OFFICIAL_COUNTS = {
    "Nutwood Structure": 582,
    "State College Structure": 1054,
    "Eastside North": 391,
    "Eastside South": 0,
    "S8 / S10": 47,
}


def structure_status(available):
    if available <= 0:
        return "full"
    if available < 100:
        return "low"
    return "open"


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def create_app(account_service=None, parking_repo=None):
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT),
        static_folder=str(PROJECT_ROOT / "css"),
        static_url_path="/css",
    )
    # Signs the session cookie. Set SECRET_KEY in your environment for real use.
    app.secret_key = os.environ.get("SECRET_KEY", "dev-only-change-me")

    service = account_service or AccountService(SQLiteUserRepository(DB_PATH))
    parking = parking_repo or ParkingLogRepository(DB_PATH)

    @app.template_filter("clock")
    def clock(timestamp):
        return datetime.fromtimestamp(timestamp).strftime("%b %d, %I:%M %p")

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
            except ValueError as error:
                return (
                    render_template("login.html", error_message=str(error)),
                    401,
                )
            except RuntimeError:
                # Lockout tried to send a verification email but none is configured.
                return (
                    render_template(
                        "login.html",
                        error_message="Too many failed attempts. Try again later.",
                    ),
                    401,
                )
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

    @app.post("/dashboard/park")
    @login_required
    def log_parking():
        try:
            parking.log_parking(
                session["user_id"],
                request.form.get("structure", ""),
                request.form.get("level", ""),
            )
        except ValueError as error:
            flash(str(error), "error")
        else:
            flash("Parking logged. Thanks for helping fellow students!")
        return redirect(url_for("dashboard"))

    @app.post("/dashboard/leave")
    @login_required
    def leave_parking():
        parking.mark_left(session["user_id"])
        flash("Marked as left. Safe travels!")
        return redirect(url_for("dashboard"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

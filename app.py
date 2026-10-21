from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

from account_creation.account_creation.accountlogic import AccountService
from account_creation.account_creation.storage import SQLiteUserRepository


PROJECT_ROOT = Path(__file__).resolve().parent


def create_app(account_service=None):
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT),
        static_folder=str(PROJECT_ROOT / "css"),
        static_url_path="/css",
    )
    service = account_service or AccountService(
        SQLiteUserRepository(str(PROJECT_ROOT / "parking_accounts.db"))
    )

    @app.get("/")
    def home():
        return render_template("index.html")

    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        form_data = {
            "first_name": "",
            "last_name": "",
            "email": "",
        }
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
            service.create_account(
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

        return redirect(url_for("login", registered="1"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "")
            password = request.form.get("password", "")
            try:
                service.login(email, password)
            except ValueError:
                return (
                    render_template(
                        "login.html",
                        error_message="Invalid email or password.",
                    ),
                    401,
                )
            return redirect(url_for("home"))

        return render_template(
            "login.html",
            success_message=(
                "Account created. Please log in."
                if request.args.get("registered") == "1"
                else None
            ),
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

import os
from flask import Blueprint, render_template, request, session, redirect, url_for

auth_bp = Blueprint("auth", __name__)


def is_authenticated() -> bool:
    return session.get("authenticated") is True


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated():
        return redirect(url_for("onboarding.onboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == os.environ.get("ADMIN_USERNAME") and password == os.environ.get("ADMIN_PASSWORD"):
            session["authenticated"] = True
            return redirect(url_for("onboarding.onboard"))
        error = "Invalid username or password."

    return render_template("login.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

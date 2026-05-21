import os
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Credentials are read at startup from the environment. Tests monkeypatch these
# module-level names directly (see tests/conftest.py), which works because Python
# resolves module globals at call time, not definition time.
APP_USERNAME = os.environ.get("APP_USERNAME", "")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")

DIVI_TEMPLATES = [
    "Classic Author",
    "Modern Minimalist",
    "Bold & Bright",
    "Cozy Romance",
    "Thriller Dark",
    "Literary Fiction",
]


def is_authenticated():
    return session.get("authenticated") is True


@app.route("/")
def index():
    return redirect(url_for("onboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if is_authenticated():
        return redirect(url_for("onboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == APP_USERNAME and password == APP_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("onboard"))
        error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/onboard")
def onboard():
    if not is_authenticated():
        return redirect(url_for("login"))
    return render_template("onboard.html", divi_templates=DIVI_TEMPLATES)


@app.route("/generate", methods=["POST"])
def generate():
    # Return 401 JSON (not a redirect) because this endpoint is called via fetch().
    if not is_authenticated():
        return jsonify({"status": "error", "message": "Not authenticated."}), 401
    # Stub — provisioning logic will be implemented in a later phase.
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)

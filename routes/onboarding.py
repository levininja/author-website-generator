from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from routes.auth import is_authenticated

onboarding_bp = Blueprint("onboarding", __name__)

DIVI_TEMPLATES = [
    "Classic Author",
    "Modern Minimalist",
    "Bold & Bright",
    "Cozy Romance",
    "Thriller Dark",
    "Literary Fiction",
]


@onboarding_bp.route("/")
def index():
    return redirect(url_for("onboarding.onboard"))


@onboarding_bp.route("/onboard")
def onboard():
    if not is_authenticated():
        return redirect(url_for("auth.login"))
    return render_template("onboard.html", divi_templates=DIVI_TEMPLATES)


@onboarding_bp.route("/generate", methods=["POST"])
def generate():
    # Return 401 JSON (not a redirect) because this endpoint is called via fetch().
    if not is_authenticated():
        return jsonify({"status": "error", "message": "Not authenticated."}), 401
    # Stub — provisioning logic will be implemented in a later milestone.
    return jsonify({"status": "ok"})

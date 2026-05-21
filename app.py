import os
from flask import Flask
from dotenv import load_dotenv

from config.loader import load_config
from routes.auth import auth_bp
from routes.onboarding import onboarding_bp

load_dotenv()


def create_app(config_path: str = "config/config.yaml") -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

    app.config["site_config"] = load_config(config_path)

    app.register_blueprint(auth_bp)
    app.register_blueprint(onboarding_bp)

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)

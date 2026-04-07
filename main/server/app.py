"""Main application factory and startup logic."""

import os
from flask import Flask, jsonify
from main.server.config import get_config
from main.server.errors import register_error_handlers


def validate_env(config_class) -> None:
    """Ensure production has required database configuration."""
    if not config_class.INIT_DB:
        return

    missing = []
    # FIX: Explicitly fail if MONGO_URI is missing or points to localhost
    if not config_class.MONGO_URI or \
            config_class.MONGO_URI.startswith("mongodb://localhost"):
        missing.append("MONGO_URI")
    if not config_class.DB_NAME:
        missing.append("DB_NAME")

    if missing:
        raise EnvironmentError(
            "Missing required environment variables: " + ", ".join(missing)
        )


def create_app(config_name=None):
    """Factory to create and configure the Flask application."""
    env_name = os.getenv("FLASK_ENV", "development")
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "application", "templates"),
        static_folder=os.path.join(base_dir, "application", "static"),
        static_url_path="/static",
    )

    config_class = get_config(config_name or env_name)
    app.config.from_object(config_class)

    # Validate prod environment when running externally
    if env_name.lower() == "production":
        validate_env(config_class)

    register_error_handlers(app)

    # Blueprint imports deferred to avoid circular dependency
    from main.application.auth import auth_bp
    from main.application.dashboard import dashboard_bp
    from main.application.logs import logs_bp
    from main.application.profile import profile_bp
    from main.server.routes.health import health_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(health_bp)

    @app.get("/")
    def index():
        return jsonify({"message": "Welcome to VitalAI"}), 200

    return app


# Expose singleton for WSGI/Gunicorn
app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = app.config.get("DEBUG", False)
    app.run(debug=debug, host="0.0.0.0", port=port)

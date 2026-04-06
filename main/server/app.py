import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template

from main.persistence.extensions import mongo
from main.server.config import get_config
from main.server.errors import register_error_handlers


def create_app(config_name=None):
    load_dotenv()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "application", "templates"),
        static_folder=os.path.join(base_dir, "application", "static"),
        static_url_path="/static",
    )

    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Initialize the database connection with the Flask app
    if app.config.get("INIT_DB", True):
        mongo.init_app(app)

    register_error_handlers(app)

    from main.application.auth import auth_bp
    from main.application.dashboard import dashboard_bp
    from main.application.logs import logs_bp
    from main.application.profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(dashboard_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/login")
    def login_page():
        return render_template("login.html")

    @app.get("/register")
    def register_page():
        return render_template("register.html")

    @app.get("/dashboard")
    def dashboard_page():
        return render_template("dashboard.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "OK"}), 200

    return app


# Module-level app instance for gunicorn WSGI
app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = app.config.get("DEBUG", False)
    app.run(debug=debug, host="0.0.0.0", port=port)

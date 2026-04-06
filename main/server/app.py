import os

from flask import Flask, jsonify

from main.persistence.extensions import mongo
from main.server.config import get_config
from main.server.errors import register_error_handlers


def create_app(config_name=None):
    app = Flask(__name__)

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
        return """
        <!doctype html>
        <html lang="en">
            <head>
                <meta charset="utf-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <title>VitalAI</title>
            </head>
            <body>
                <h1>VitalAI</h1>
                <p>
                    <a href="/health">Health Check</a>
                </p>
            </body>
        </html>
        """

    @app.get("/health")
    def health():
        return jsonify({"status": "OK"}), 200

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = app.config.get("DEBUG", False)
    app.run(debug=debug, host="0.0.0.0", port=port)

import os
import sys

from flask import Flask, jsonify


def create_app():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from main.persistence.database import db

    app = Flask(__name__)

    # Initialize the database connection with the Flask app
    db.init_app(app)

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
    env = os.getenv("FLASK_ENV", "production")
    debug = env.lower() != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)

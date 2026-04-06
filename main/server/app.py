import os
import sys

from dotenv import load_dotenv

load_dotenv()

# ── Fix Python paths ─────────────────────────────────────────────────────────
# 1. Add project root so 'main.*' imports resolve
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 2. Add main/persistence so bare 'from database import get_db' resolves
persistence_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "persistence"))
if persistence_path not in sys.path:
    sys.path.insert(0, persistence_path)

from flask import Flask, jsonify


def create_app():
    app = Flask(
        __name__,
        template_folder="../application/templates",
        static_folder="../application/static",
    )

    # ── Load config ───────────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

    # ── Database ──────────────────────────────────────────────────────────────
    from main.persistence.database import db
    db.init_app(app)

    # ── Blueprints ────────────────────────────────────────────────────────────
    from main.application.routes.index_routes import index_bp
    from main.application.routes.auth_routes import auth_bp
    from main.application.routes.dashboard_routes import dashboard_bp
    from main.application.routes.meal_routes import meal_bp
    from main.application.routes.workout_routes import workout_bp
    from main.application.routes.sleep_routes import sleep_bp
    from main.application.routes.hydration_routes import hydration_bp
    from main.application.routes.mood_routes import mood_bp
    from main.application.routes.insights_routes import insights_bp

    app.register_blueprint(index_bp)       # GET /
    app.register_blueprint(auth_bp)        # GET /login, GET /register, POST /api/login, POST /api/register
    app.register_blueprint(dashboard_bp)   # GET /dashboard
    app.register_blueprint(meal_bp)        # GET/POST /api/meals
    app.register_blueprint(workout_bp)     # GET/POST /api/workouts
    app.register_blueprint(sleep_bp)       # GET/POST /api/sleep
    app.register_blueprint(hydration_bp)   # GET/POST /api/hydration
    app.register_blueprint(mood_bp)        # GET/POST /api/moods
    app.register_blueprint(insights_bp)    # GET /api/insights/weekly

    # ── Health check ─────────────────────────────────────────────────────────
    @app.get("/health")
    def health():
        db_status = "OK"
        try:
            db.client.admin.command("ping")
        except Exception:
            db_status = "Disconnected"
        return jsonify({"status": "OK", "database": db_status}), 200

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_ENV", "production").lower() != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
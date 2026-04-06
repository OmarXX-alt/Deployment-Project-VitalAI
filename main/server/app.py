from flask import Flask, jsonify
from main.persistence.database import db

from main.application.routes.index_routes import index_bp
from main.application.routes.auth_routes import auth_bp
from main.application.routes.dashboard_routes import dashboard_bp
from main.application.routes.meal_routes import meal_bp
from main.application.routes.workout_routes import workout_bp
from main.application.routes.sleep_routes import sleep_bp
from main.application.routes.hydration_routes import hydration_bp
from main.application.routes.mood_routes import mood_bp
from main.application.routes.insights_routes import insights_bp

app = Flask(__name__, template_folder="../application/templates", static_folder="../application/static")

# Initialize the database connection with the Flask app
db.init_app(app)

# ── Register blueprints ──────────────────────────────────────────────────────
app.register_blueprint(index_bp)       # GET /
app.register_blueprint(auth_bp)        # GET /login, GET /register, POST /api/login, POST /api/register
app.register_blueprint(dashboard_bp)   # GET /dashboard
app.register_blueprint(meal_bp)        # GET/POST /api/meals
app.register_blueprint(workout_bp)     # GET/POST /api/workouts
app.register_blueprint(sleep_bp)       # GET/POST /api/sleep
app.register_blueprint(hydration_bp)   # GET/POST /api/hydration
app.register_blueprint(mood_bp)        # GET/POST /api/moods
app.register_blueprint(insights_bp)    # GET /api/insights/weekly


@app.get("/health")
def health():
    db_status = "OK"
    try:
        db.client.admin.command('ping')
    except Exception:
        db_status = "Disconnected"

    return jsonify({
        "status": "OK",
        "database": db_status
    }), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
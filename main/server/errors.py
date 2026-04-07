from flask import jsonify
from pymongo.errors import ServerSelectionTimeoutError


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(ServerSelectionTimeoutError)
    def handle_db_timeout(error):
        # FIX: Connection timeout mid-request returns safe 503 instead of crash
        app.logger.exception("Database connection timeout: %s", error)
        return jsonify({"error": "Service Currently Unavailable"}), 503

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("Unhandled error: %s", error)
        return jsonify({"error": "Internal Server Error"}), 500

    return app

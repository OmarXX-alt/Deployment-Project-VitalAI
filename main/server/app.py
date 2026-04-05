from flask import Flask, jsonify
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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

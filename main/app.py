from flask import Flask, jsonify


app = Flask(__name__)


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


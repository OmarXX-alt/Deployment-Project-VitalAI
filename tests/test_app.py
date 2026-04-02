import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main.application.app import app


def test_index_route_returns_html():
    client = app.test_client()
    response = client.get("/")

    assert response.status_code == 200
    assert b"<!doctype html>" in response.data


def test_health_route_returns_ok():
    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "OK"}

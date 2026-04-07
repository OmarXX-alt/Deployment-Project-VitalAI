import os

import pytest

# Ensure tests always use the testing config.
os.environ["FLASK_ENV"] = "testing"

from main.server.app import create_app


@pytest.fixture(name="app")
def app_fixture():
    """Create a Flask app configured for testing."""

    app = create_app("testing")
    return app


@pytest.fixture(name="client")
def client_fixture(app):
    """Provide a test client for Flask routes."""

    return app.test_client()

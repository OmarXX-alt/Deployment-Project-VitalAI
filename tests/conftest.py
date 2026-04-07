"""Pytest fixtures and environment preparation."""

import os
import pytest

# FIX: Set testing config before the app is instantiated (Rule 4)
os.environ["FLASK_ENV"] = "testing"
from main.server.app import create_app  # noqa: E402


@pytest.fixture(name="app")
def app_fixture():
    """Provide a Flask test application instance."""
    app = create_app("testing")
    return app


@pytest.fixture(name="client")
def client_fixture(app):
    """Provide a test client for route execution."""
    return app.test_client()

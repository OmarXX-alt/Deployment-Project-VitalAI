from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from bson import ObjectId

from main.application import chat as chat_module
from main.business import ai_service


def _make_token(client, user_id):
    secret = client.application.config["JWT_SECRET"]
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def _auth_headers(client, user_id):
    token = _make_token(client, user_id)
    return {"Authorization": f"Bearer {token}"}


class FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeCollection:
    def __init__(self):
        self.docs = {}

    def find_one(self, query):
        for doc in self.docs.values():
            if doc.get("_id") == query.get("_id") and doc.get(
                "user_id"
            ) == query.get("user_id"):
                return doc
        return None

    def insert_one(self, doc):
        new_id = ObjectId()
        stored = dict(doc)
        stored["_id"] = new_id
        self.docs[new_id] = stored
        return FakeInsertResult(new_id)

    def update_one(self, query, update):
        doc = self.find_one(query)
        if not doc:
            return None
        if isinstance(update, dict) and "$set" in update:
            doc.update(update["$set"])
        return None


class FakeDB:
    def __init__(self):
        self.chat_sessions = FakeCollection()

    def __getitem__(self, name):
        if name == "chat_sessions":
            return self.chat_sessions
        raise KeyError(name)


def test_chat_creates_session(client, monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(chat_module, "get_db", lambda: fake_db)
    monkeypatch.setattr(
        chat_module.aggregation_service,
        "build_context",
        lambda *args, **kwargs: {"ctx": "ok"},
    )

    def fake_chat_response(*args, **kwargs):
        return "Hello"

    monkeypatch.setattr(
        ai_service, "get_chat_response", fake_chat_response
    )

    user_id = str(ObjectId())
    response = client.post(
        "/api/chat",
        headers=_auth_headers(client, user_id),
        json={"message": "Hi"},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["reply"] == "Hello"
    assert data["session_id"]
    assert len(fake_db.chat_sessions.docs) == 1

    stored = next(iter(fake_db.chat_sessions.docs.values()))
    assert len(stored["messages"]) == 2


def test_chat_reuses_session(client, monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(chat_module, "get_db", lambda: fake_db)
    monkeypatch.setattr(
        chat_module.aggregation_service,
        "build_context",
        lambda *args, **kwargs: {"ctx": "ok"},
    )

    def fake_chat_response_first(*args, **kwargs):
        return "First"

    monkeypatch.setattr(
        ai_service, "get_chat_response", fake_chat_response_first
    )

    user_id = str(ObjectId())
    first = client.post(
        "/api/chat",
        headers=_auth_headers(client, user_id),
        json={"message": "Hello"},
    )
    session_id = first.get_json()["session_id"]

    def fake_chat_response_second(*args, **kwargs):
        return "Second"

    monkeypatch.setattr(
        ai_service, "get_chat_response", fake_chat_response_second
    )

    second = client.post(
        "/api/chat",
        headers=_auth_headers(client, user_id),
        json={"message": "Follow-up", "session_id": session_id},
    )

    assert second.status_code == 200
    stored = next(iter(fake_db.chat_sessions.docs.values()))
    assert len(stored["messages"]) == 4
    assert stored["messages"][-1]["content"] == "Second"


def test_chat_invalid_session_id(client, monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(chat_module, "get_db", lambda: fake_db)

    user_id = str(ObjectId())
    response = client.post(
        "/api/chat",
        headers=_auth_headers(client, user_id),
        json={"message": "Hi", "session_id": "bad-id"},
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "invalid_session_id"


def mock_build_context(*args, **kwargs):
    """Mock context builder that tracks calls."""
    return {"ctx": "ok"}


def test_chat_lightweight_mode(client, monkeypatch):
    """Test lightweight mode skips context loading for faster responses."""
    fake_db = FakeDB()
    monkeypatch.setattr(chat_module, "get_db", lambda: fake_db)

    monkeypatch.setattr(
        chat_module.aggregation_service,
        "build_context",
        mock_build_context,
    )

    def fake_chat_response_lightweight(*args, **kwargs):
        return "Response"

    monkeypatch.setattr(
        ai_service, "get_chat_response", fake_chat_response_lightweight
    )

    user_id = str(ObjectId())

    # Test lightweight mode - should skip context
    response = client.post(
        "/api/chat",
        headers=_auth_headers(client, user_id),
        json={"message": "Hi", "lightweight": True},
    )

    assert response.status_code == 200
    assert response.get_json()["reply"] == "Response"


def test_chat_short_message_skips_context(client, monkeypatch):
    """Test that short messages (greetings) skip context loading."""
    fake_db = FakeDB()
    monkeypatch.setattr(chat_module, "get_db", lambda: fake_db)

    def track_context(*args, **kwargs):
        return {"ctx": "ok"}

    monkeypatch.setattr(
        chat_module.aggregation_service,
        "build_context",
        track_context,
    )

    def fake_chat_response_short(*args, **kwargs):
        return "Hi there!"

    monkeypatch.setattr(
        ai_service, "get_chat_response", fake_chat_response_short
    )

    user_id = str(ObjectId())

    # Test short message
    response = client.post(
        "/api/chat",
        headers=_auth_headers(client, user_id),
        json={"message": "Hi"},
    )
    assert response.status_code == 200
    assert response.get_json()["reply"] == "Hi there!"

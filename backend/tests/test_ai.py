def test_ai_chat_without_api_key(client, auth_a):
    response = client.post("/api/ai/chat", headers=auth_a, json={"message": "Which products need restocking today?"})
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert "GEMINI_API_KEY" in detail
    assert "Inventory" in detail


def test_ai_chat_rejects_empty_message(client, auth_a):
    response = client.post("/api/ai/chat", headers=auth_a, json={"message": "   "})
    assert response.status_code == 422


def test_ai_requires_auth(client):
    response = client.post("/api/ai/chat", json={"message": "hello"})
    assert response.status_code == 401


def test_ai_falls_back_to_groq(client, auth_a, monkeypatch):
    from app.config import get_settings
    from app.services import gemini_service

    settings = get_settings()
    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini")
    monkeypatch.setattr(settings, "groq_api_key", "test-groq")

    def fail_gemini(_settings, _prompt):
        raise RuntimeError("gemini unavailable")

    def groq_ok(_settings, _prompt):
        return "Cooking oil is below the minimum stock.", "llama-3.1-8b-instant"

    monkeypatch.setattr(gemini_service, "_call_gemini", fail_gemini)
    monkeypatch.setattr(gemini_service, "_call_groq", groq_ok)

    response = client.post(
        "/api/ai/chat",
        headers=auth_a,
        json={"message": "Which products need restocking today?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "groq"
    assert body["model"] == "llama-3.1-8b-instant"
    assert "oil" in body["reply"].lower()

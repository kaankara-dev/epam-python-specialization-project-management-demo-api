from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_s3_event_webhook_forwards_event_to_handler_and_returns_result(client):
    """Endpoint, gelen event'i olduğu gibi handler'a iletmeli ve handler'ın
    döndürdüğü sonucu 200 OK ile geri vermeli."""
    fake_event = {
        "Records": [
            {"s3": {"object": {"key": "projects/1/x.pdf", "size": 2048}}}
        ]
    }

    with patch("app.api.v1.endpoints.internal.handler") as mock_handler:
        mock_handler.return_value = {"updated": [1], "not_found": []}

        res = client.post("/api/v1/internal/s3-events", json=fake_event)

    assert res.status_code == 200
    assert res.json() == {"updated": [1], "not_found": []}
    mock_handler.assert_called_once_with(fake_event, None)


def test_s3_event_webhook_with_unmatched_key(client):
    """Handler bir key'i bulamadığını raporladığında endpoint bunu olduğu
    gibi yansıtmalı (hata fırlatmadan)."""
    fake_event = {"Records": [{"s3": {"object": {"key": "ghost.pdf", "size": 1}}}]}

    with patch("app.api.v1.endpoints.internal.handler") as mock_handler:
        mock_handler.return_value = {"updated": [], "not_found": ["ghost.pdf"]}

        res = client.post("/api/v1/internal/s3-events", json=fake_event)

    assert res.status_code == 200
    assert res.json()["not_found"] == ["ghost.pdf"]
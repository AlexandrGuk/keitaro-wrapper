def test_pages_and_api_are_registered():
    from fastapi.testclient import TestClient

    from app.config import settings
    from app.main import app
    from app.naming import NamingError
    from app.shares import ShareError

    settings.app_username = "guk"
    settings.app_password = "secret"

    assert NamingError in app.exception_handlers
    assert ShareError in app.exception_handlers

    client = TestClient(app)
    locked = client.get("/", follow_redirects=False)
    assert locked.status_code == 303
    assert locked.headers["location"] == "login"
    assert "Обёртка Keitaro" in client.get("/login").text
    assert client.get("/api/prefix").status_code == 401
    assert client.post("/api/login", json={"username": "guk", "password": "no"}).status_code == 401

    logged_in = client.post("/api/login", json={"username": "guk", "password": "secret"})
    assert logged_in.status_code == 200
    assert client.get("/").status_code == 200
    assert client.get("/campaigns").status_code == 200
    assert client.get("/campaign").status_code == 200
    assert client.get("/api/prefix").json() == {"prefix": "test_guk_"}
    missing = client.get("/api/domains")
    assert missing.status_code == 500
    assert "KEITARO_API_KEY" in missing.json()["detail"]
    assert client.post("/api/logout").status_code == 200
    assert client.get("/api/prefix").status_code == 401

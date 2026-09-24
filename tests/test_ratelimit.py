import importlib

import ratelimit


def test_bucket_for_login_uses_stricter_limit():
    assert ratelimit._bucket_for("/api/login") == ("/api/login", 5, 10)


def test_bucket_for_generic_api_path():
    assert ratelimit._bucket_for("/api/state") == ("/api/", 30, 10)


def test_bucket_for_non_api_path_is_unlimited():
    assert ratelimit._bucket_for("/index.html") is None


def test_middleware_blocks_after_limit_exceeded(monkeypatch):
    # Reload to get a clean _hits dict, independent of whatever main.py's
    # TestClient fixture has already recorded against this same module.
    rl = importlib.reload(ratelimit)
    from starlette.testclient import TestClient
    from fastapi import FastAPI

    app = FastAPI()
    app.add_middleware(rl.RateLimitMiddleware)

    @app.get("/api/login")
    def fake_login():
        return {"ok": True}

    client = TestClient(app)
    responses = [client.get("/api/login") for _ in range(6)]
    statuses = [r.status_code for r in responses]

    assert statuses.count(200) == 5  # the limit
    assert statuses.count(429) == 1  # the 6th request is blocked

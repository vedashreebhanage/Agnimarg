import time

import auth


def test_verify_credentials_correct_password():
    user = auth.verify_credentials("authority1", "demo-authority-pass")
    assert user == {"username": "authority1", "role": "authority"}


def test_verify_credentials_wrong_password():
    assert auth.verify_credentials("authority1", "wrong-password") is None


def test_verify_credentials_unknown_user():
    assert auth.verify_credentials("nobody", "whatever") is None


def test_issue_and_verify_token_roundtrip():
    token = auth.issue_token("authority1", "authority")
    payload = auth.verify_token(token)
    assert payload["username"] == "authority1"
    assert payload["role"] == "authority"


def test_verify_token_rejects_tampered_token():
    token = auth.issue_token("citizen1", "citizen")
    body, signature = token.split(".", 1)
    tampered = f"{body}x.{signature}"  # corrupt the payload, keep the old signature
    assert auth.verify_token(tampered) is None


def test_verify_token_rejects_garbage():
    assert auth.verify_token("not-a-real-token") is None
    assert auth.verify_token("") is None


def test_verify_token_rejects_expired(monkeypatch):
    token = auth.issue_token("authority1", "authority")
    # jump the clock past the TTL — capture real time first, since auth.time
    # IS the same `time` module object the test imports (patching one patches
    # both), so a lambda calling time.time() here would recurse into itself.
    future = time.time() + auth.TOKEN_TTL_SECONDS + 60
    monkeypatch.setattr(auth.time, "time", lambda: future)
    assert auth.verify_token(token) is None

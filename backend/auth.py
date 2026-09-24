"""Minimal username/password auth with signed session tokens.

Per the Prototype Plan doc's security table: "Authentication: Yes (basic)".
This replaces an earlier version of the demo where the dispatch-approval
endpoint simply trusted a client-supplied `role` field — anyone could call the
API directly with role="authority" and skip the login UI entirely. Now the
server derives role from a signed token it issued, not from client input.

Demo credentials are intentionally public (shown in the login form's
placeholder text) — this is a college-project demo, not a real security
boundary. Passwords are SHA-256 hashed rather than plaintext-compared mostly
to model the right shape of the check, not as a real production claim.
"""
import base64
import hashlib
import hmac
import json
import os
import time

_DEFAULT_AUTH_SECRET = "demo-only-not-for-production-auth-key"
AUTH_SECRET = os.environ.get("AGNIMARG_AUTH_SECRET", _DEFAULT_AUTH_SECRET).encode()
USING_DEFAULT_AUTH_SECRET = AUTH_SECRET == _DEFAULT_AUTH_SECRET.encode()
TOKEN_TTL_SECONDS = 2 * 60 * 60  # 2 hours — long enough for one review session


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# Deliberately public demo credentials — see module docstring.
DEMO_USERS = {
    "authority1": {"password_hash": _hash("demo-authority-pass"), "role": "authority"},
    "citizen1": {"password_hash": _hash("demo-citizen-pass"), "role": "citizen"},
}


def verify_credentials(username: str, password: str) -> dict | None:
    user = DEMO_USERS.get(username)
    if not user or not hmac.compare_digest(user["password_hash"], _hash(password)):
        return None
    return {"username": username, "role": user["role"]}


def issue_token(username: str, role: str) -> str:
    payload = {"username": username, "role": role, "issued_at": time.time(), "expires_at": time.time() + TOKEN_TTL_SECONDS}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(AUTH_SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def verify_token(token: str) -> dict | None:
    try:
        body, signature = token.split(".", 1)
    except ValueError:
        return None
    expected = hmac.new(AUTH_SECRET, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None
    try:
        payload = json.loads(base64.urlsafe_b64decode(body.encode()))
    except (ValueError, json.JSONDecodeError):
        return None
    if payload.get("expires_at", 0) < time.time():
        return None
    return payload

"""Run: python checks/admin_login.py (local HTTP only, no browser/upstream)."""
import os
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time

import requests
import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

with tempfile.TemporaryDirectory() as home:
    os.environ.update(MUSE2API_HOME=home, MUSE2API_ADMIN_USERNAME="test-admin",
                      MUSE2API_ADMIN_PASSWORD="test-password", MUSE2API_KEY="test-api")
    import app as module

    module.CFG.base_dir = str(ROOT)
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    base = f"http://127.0.0.1:{sock.getsockname()[1]}"
    server = uvicorn.Server(uvicorn.Config(module.app, lifespan="off", log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    client = requests.Session()
    client.trust_env = False
    def request(method, path, **kwargs):
        return client.request(method, base + path, timeout=5, allow_redirects=False, **kwargs)
    credentials = {"username": "test-admin", "password": "test-password"}
    headers = {"Origin": base, "X-Admin-Request": "1"}
    module.CFG.public_base = base
    try:
        for _ in range(100):
            if server.started:
                break
            time.sleep(.05)
        assert server.started
        assert request("GET", "/admin").status_code == 303
        assert request("GET", "/login").status_code == 200
        for path in ("/admin/accounts", "/admin/apikey", "/admin/update/check", "/openapi.json"):
            assert request("GET", path, headers={"Authorization": "Bearer test-api"}).status_code == 401
        assert request("GET", "/v1/models", headers={"Authorization": "Bearer test-api"}).status_code == 200
        assert request("GET", "/v1/models").status_code == 401
        assert request("POST", "/login", json=credentials).status_code == 403
        assert request("POST", "/login", json={**credentials, "password": "wrong"}, headers=headers).status_code == 401
        response = request("POST", "/login", json=credentials, headers=headers)
        assert response.status_code == 200
        assert "HttpOnly" in response.headers["Set-Cookie"]
        assert "SameSite=strict" in response.headers["Set-Cookie"]
        assert request("GET", "/admin").status_code == 200
        assert request("GET", "/admin/apikey").json()["api_key"] == "test-api"
        assert request("POST", "/admin/logout").status_code == 403
        assert request("POST", "/admin/logout", headers={**headers, "Origin": "https://evil.invalid"}).status_code == 403
        token = client.cookies.get(module._ADMIN_COOKIE)
        assert request("POST", "/admin/logout", headers=headers).status_code == 200
        assert token not in module._ADMIN_SESSIONS
        assert request("GET", "/admin/accounts").status_code == 401
        assert request("POST", "/login", json=credentials, headers=headers).status_code == 200
        module._ADMIN_SESSIONS[client.cookies.get(module._ADMIN_COOKIE)] = time.time() - 1
        assert request("GET", "/admin/accounts").status_code == 401
        module.CFG.admin_password = ""
        assert request("POST", "/login", json=credentials, headers=headers).status_code == 503
        module.CFG.admin_password = "test-password"
        module._LOGIN_ATTEMPTS[:] = [time.time()] * 10
        assert request("POST", "/login", json=credentials, headers=headers).status_code == 429
        print("PASS: admin isolation, login, CSRF, logout, expiry, fail-closed, throttle, API key")
    finally:
        client.close()
        server.should_exit = True
        thread.join(timeout=10)
        sock.close()

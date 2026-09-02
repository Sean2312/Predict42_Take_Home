#!/usr/bin/env python3
"""A small, deliberately annoying stand-in for a vendor case API.

Start it with::

    python -m fake_api.server           # listens on http://127.0.0.1:8080

Endpoints
---------
``POST /oauth/token``
    OAuth2 client_credentials. Form or JSON body with ``client_id`` and
    ``client_secret`` (see README for the values). Returns
    ``{"access_token": ..., "expires_in": 120}``.

``GET /api/cases?closed_on=YYYY-MM-DD&offset=0&limit=100``
    Cases closed on that day.

``GET /api/cases/updated?since=YYYY-MM-DD&offset=0&limit=100``
    Every case revision modified at or after ``since``.

Both list endpoints need ``Authorization: Bearer <token>`` and answer with
``{"items": [...], "offset": ..., "limit": ...}``.
"""

import json
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from fake_api.data import DATASET

CLIENT_ID = "trainee-task"
CLIENT_SECRET = "s3cret-do-not-tell"
TOKEN_TTL_SECONDS = 120
DEFAULT_LIMIT = 100
MAX_LIMIT = 500
PAGE_OVERLAP = 5

_tokens: dict[str, float] = {}
_request_count = 0


def _parse_ts(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _closed_on(case: dict, day: str) -> bool:
    return bool(case["closed_at"]) and case["closed_at"].startswith(day)


def _modified_since(case: dict, since: str) -> bool:
    return _parse_ts(case["last_modified"]) >= datetime.strptime(
        since, "%Y-%m-%d"
    ).replace(tzinfo=timezone.utc)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # noqa: A002 - quieter console
        print(f"  {self.command} {self.path} -> {args[1]}")

    # -- plumbing ---------------------------------------------------------
    def _send(self, status: int, payload: dict, extra_headers: dict | None = None):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra_headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _flaky(self) -> bool:
        """Every 7th request fails, every 11th is rate limited.

        Deterministic on purpose: everyone hits the same bumps.
        """
        global _request_count
        _request_count += 1
        if _request_count % 11 == 0:
            self._send(
                429,
                {"error": "rate limit exceeded"},
                {"Retry-After": "2"},
            )
            return True
        if _request_count % 7 == 0:
            self._send(503, {"error": "backend temporarily unavailable"})
            return True
        return False

    def _authorized(self) -> bool:
        header = self.headers.get("Authorization", "")
        token = header[7:] if header.startswith("Bearer ") else ""
        issued = _tokens.get(token)
        if issued is None:
            self._send(401, {"error": "missing or unknown token"})
            return False
        if time.monotonic() - issued > TOKEN_TTL_SECONDS:
            self._send(401, {"error": "token expired"})
            return False
        return True

    def _page(self, rows: list[dict], query: dict) -> None:
        try:
            offset = int(query.get("offset", ["0"])[0])
            limit = int(query.get("limit", [str(DEFAULT_LIMIT)])[0])
        except ValueError:
            self._send(400, {"error": "offset and limit must be integers"})
            return
        if offset < 0 or limit < 1:
            self._send(400, {"error": "offset must be >= 0 and limit >= 1"})
            return
        limit = min(limit, MAX_LIMIT)
        # pages overlap, so the same record can be handed out twice
        start = max(0, offset - PAGE_OVERLAP) if offset else 0
        self._send(
            200,
            {"items": rows[start : offset + limit], "offset": offset, "limit": limit},
        )

    # -- routes -----------------------------------------------------------
    def do_POST(self):  # noqa: N802
        if urlparse(self.path).path != "/oauth/token":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode()
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {k: v[0] for k, v in parse_qs(raw).items()}
        if (
            body.get("client_id") != CLIENT_ID
            or body.get("client_secret") != CLIENT_SECRET
        ):
            self._send(401, {"error": "invalid_client"})
            return
        token = f"tok-{int(time.monotonic() * 1000)}"
        _tokens[token] = time.monotonic()
        self._send(
            200,
            {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": TOKEN_TTL_SECONDS,
            },
        )

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/health":
            self._send(200, {"status": "ok", "records": len(DATASET)})
            return
        if parsed.path not in ("/api/cases", "/api/cases/updated"):
            self._send(404, {"error": "not found"})
            return
        if not self._authorized() or self._flaky():
            return

        if parsed.path == "/api/cases":
            day = query.get("closed_on", [None])[0]
            if not day:
                self._send(400, {"error": "closed_on is required"})
                return
            rows = [c for c in DATASET if _closed_on(c, day)]
        else:
            since = query.get("since", [None])[0]
            if not since:
                self._send(400, {"error": "since is required"})
                return
            rows = [c for c in DATASET if _modified_since(c, since)]

        self._page(rows, query)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8080), Handler)
    print(f"fake case API on http://127.0.0.1:8080 ({len(DATASET)} records)")
    print("  POST /oauth/token")
    print("  GET  /api/cases?closed_on=2026-07-14&offset=0&limit=100")
    print("  GET  /api/cases/updated?since=2026-07-14&offset=0&limit=100")
    server.serve_forever()


if __name__ == "__main__":
    main()

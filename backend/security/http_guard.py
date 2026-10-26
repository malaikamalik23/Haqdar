"""HTTP-level protections for the Haqdar API (module A7).

Three small ASGI middlewares with no extra dependencies:
  SecurityHeadersMiddleware  adds browser security headers and stops responses being cached
  BodySizeLimitMiddleware    rejects oversized request bodies, even when streamed without a length
  RateLimitMiddleware        per-client sliding-window limit kept in memory

Nothing here reads, stores or logs request bodies.
"""
import json
import math
import time
from collections import OrderedDict, deque


def _json_response(status, detail, extra_headers=()):
    body = json.dumps({"detail": detail}).encode()
    headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
    headers.extend(extra_headers)
    return [{"type": "http.response.start", "status": status, "headers": headers},
            {"type": "http.response.body", "body": body}]


async def _send_all(send, messages):
    for message in messages:
        await send(message)


class SecurityHeadersMiddleware:
    """Adds security headers to every response, including errors produced by the other guards."""

    def __init__(self, app, *, hsts=False, relaxed_paths=("/docs", "/redoc", "/openapi.json")):
        self.app = app
        self.hsts = hsts
        self.relaxed_paths = tuple(relaxed_paths)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        relaxed = scope["path"] in self.relaxed_paths

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                present = {k.lower() for k, _ in headers}

                def add(name, value):
                    if name not in present:
                        headers.append((name, value))

                add(b"x-content-type-options", b"nosniff")
                add(b"x-frame-options", b"DENY")
                add(b"referrer-policy", b"no-referrer")
                add(b"permissions-policy", b"camera=(), microphone=(), geolocation=()")
                add(b"cache-control", b"no-store")  # answers can contain personal context
                if not relaxed:  # the interactive docs page needs scripts, so it is exempt
                    add(b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'")
                if self.hsts:
                    add(b"strict-transport-security", b"max-age=31536000; includeSubDomains")
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)


class _TooLarge(Exception):
    pass


class BodySizeLimitMiddleware:
    """Rejects bodies larger than max_bytes. Checks Content-Length and also counts streamed bytes."""

    def __init__(self, app, *, max_bytes, path_max_bytes=None):
        self.app = app
        self.max_bytes = max_bytes
        self.path_max_bytes = dict(path_max_bytes or {})  # bigger limit for specific routes, e.g. /extract

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        limit = self.path_max_bytes.get(scope["path"], self.max_bytes)

        for name, value in scope["headers"]:
            if name == b"content-length":
                if value.isdigit() and int(value) > limit:
                    return await _send_all(send, _json_response(413, "Request body too large"))
                break

        received = 0
        started = False
        rejected = False

        async def counting_receive():
            nonlocal received, rejected
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    # FastAPI turns errors raised while reading the body into a 400, so the 413
                    # is sent right here, and anything the app sends afterwards is dropped.
                    if not started and not rejected:
                        rejected = True
                        await _send_all(send, _json_response(413, "Request body too large"))
                    raise _TooLarge()
            return message

        async def guarded_send(message):
            nonlocal started
            if rejected:
                return
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, counting_receive, guarded_send)
        except _TooLarge:
            pass


class RateLimitMiddleware:
    """Sliding-window limit per client. Reads and writes are counted separately.

    State is in memory, so with several server processes each one counts on its own.
    Behind a reverse proxy, set trust_proxy=True so clients are told apart by the proxy's
    X-Forwarded-For header. Only do that when a proxy you control sets the header.
    """

    WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, app, *, write_limit, read_limit, window=60.0, trust_proxy=False,
                 max_clients=10_000, clock=time.monotonic, path_limits=None):
        self.app = app
        self.limits = {"w": write_limit, "r": read_limit}
        self.path_limits = dict(path_limits or {})  # stricter limit per route, counted separately
        self.window = window
        self.trust_proxy = trust_proxy
        self.max_clients = max_clients
        self.clock = clock
        self.hits = OrderedDict()

    def _client(self, scope):
        if self.trust_proxy:
            for name, value in scope["headers"]:
                if name == b"x-forwarded-for":
                    parts = [p.strip() for p in value.decode("latin-1").split(",") if p.strip()]
                    if parts:
                        return parts[-1]  # the entry added by our own proxy
        client = scope.get("client")
        return client[0] if client else "unknown"

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] == "OPTIONS":
            return await self.app(scope, receive, send)

        path = scope["path"]
        if path in self.path_limits:
            bucket, limit = path, self.path_limits[path]
        else:
            bucket = "w" if scope["method"] in self.WRITE_METHODS else "r"
            limit = self.limits[bucket]
        key = (self._client(scope), bucket)
        now = self.clock()
        window = self.hits.get(key)
        if window is None:
            window = self.hits[key] = deque()
        while window and now - window[0] >= self.window:
            window.popleft()

        if len(window) >= limit:
            retry = max(1, math.ceil(self.window - (now - window[0])))
            return await _send_all(
                send, _json_response(429, "Too many requests. Try again later.",
                                     [(b"retry-after", str(retry).encode())]))

        window.append(now)
        self.hits.move_to_end(key)
        while len(self.hits) > self.max_clients:
            self.hits.popitem(last=False)  # forget the least recently seen client
        await self.app(scope, receive, send)
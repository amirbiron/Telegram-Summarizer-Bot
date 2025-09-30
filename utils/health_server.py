"""
Lightweight HTTP health server to satisfy Render's port check.

Runs a tiny HTTP server on the configured port in a background thread,
responding 200 OK on "/" and "/healthz".
"""

import http.server
import socketserver
import threading
from typing import Optional


class _HealthRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # type: ignore[override]
        if self.path in ("/", "/healthz", "/livez", "/readyz"):
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A003 - signature required by BaseHTTPRequestHandler
        # Silence default logging to avoid noisy output in bot logs
        return


class HealthServer:
    """Embeds a simple HTTP server in a background thread."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self._httpd: Optional[socketserver.TCPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        # Create TCPServer with reusable address to handle Render restarts gracefully
        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True

        self._httpd = ReusableTCPServer((self.host, self.port), _HealthRequestHandler)

        def serve() -> None:
            assert self._httpd is not None
            self._httpd.serve_forever()

        self._thread = threading.Thread(target=serve, name="health-server", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is not None:
            try:
                self._httpd.shutdown()
            finally:
                self._httpd.server_close()
                self._httpd = None


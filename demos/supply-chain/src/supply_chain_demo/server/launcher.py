"""Jupyter-safe background launcher and admin client for the FastAPI mock server."""

from __future__ import annotations

import threading
import time
from typing import Any

import httpx
import uvicorn

from supply_chain_demo.server.app import create_app
from supply_chain_demo.server.state import ServerState

_REGISTRY_LOCK = threading.Lock()
_ACTIVE_SERVERS: dict[tuple[str, int], MockEnterpriseServer] = {}


class MockEnterpriseServer:
    """Handle to the background FastAPI mock server running in a daemon thread."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        *,
        owns_thread: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.url = f"http://{host}:{port}"
        self._owns_thread = owns_thread
        self.state = ServerState()
        self.app = create_app(self.state)
        self._uvicorn_server: uvicorn.Server | None = None
        self._thread: threading.Thread | None = None
        self._thread_error: BaseException | None = None

    def start(self, timeout_s: float = 10.0) -> MockEnterpriseServer:
        """Start uvicorn in a daemon thread and block until /health responds 200."""
        if not self._owns_thread:
            return self

        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
            access_log=False,
        )
        server = uvicorn.Server(config)
        # Critical for Jupyter/worker threads: uvicorn cannot register SIGINT handlers off main thread.
        server.install_signal_handlers = lambda: None  # type: ignore[method-assign]
        self._uvicorn_server = server

        def _serve() -> None:
            try:
                server.run()
            except BaseException as exc:  # pragma: no cover - defensive guard
                self._thread_error = exc

        self._thread = threading.Thread(
            target=_serve,
            name=f"mock-enterprise-{self.host}:{self.port}",
            daemon=True,
        )
        self._thread.start()

        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self._thread_error is not None:
                raise RuntimeError(
                    f"MockEnterpriseServer failed to start on {self.url}"
                ) from self._thread_error
            if self.is_healthy():
                return self
            if not self._thread.is_alive():
                raise RuntimeError(f"MockEnterpriseServer thread exited unexpectedly on {self.url}")
            time.sleep(0.05)

        self.stop()
        raise TimeoutError(f"MockEnterpriseServer did not become healthy at {self.url} within {timeout_s}s.")

    def is_healthy(self) -> bool:
        """Check whether GET /health returns HTTP 200."""
        try:
            resp = httpx.get(f"{self.url}/health", timeout=0.5)
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def is_running(self) -> bool:
        """Return True if the managed server thread is alive or the target endpoint is healthy."""
        if self._owns_thread:
            return bool(self._thread and self._thread.is_alive() and self.is_healthy())
        return self.is_healthy()

    def get_metrics(self) -> dict[str, Any]:
        """Fetch recorded HTTP telemetry from GET /admin/metrics."""
        resp = httpx.get(f"{self.url}/admin/metrics", timeout=5.0)
        resp.raise_for_status()
        return resp.json()

    def reset_metrics(self) -> None:
        """Clear recorded HTTP call telemetry via POST /admin/metrics/reset."""
        resp = httpx.post(f"{self.url}/admin/metrics/reset", timeout=5.0)
        resp.raise_for_status()

    def set_faults(self, **kwargs: Any) -> dict[str, Any]:
        """Inject latency or error faults via POST /admin/faults."""
        resp = httpx.post(f"{self.url}/admin/faults", json=kwargs, timeout=5.0)
        resp.raise_for_status()
        return resp.json()

    def reset_faults(self) -> dict[str, Any]:
        """Restore default healthy latencies and failure modes via POST /admin/faults/reset."""
        resp = httpx.post(f"{self.url}/admin/faults/reset", timeout=5.0)
        resp.raise_for_status()
        return resp.json()

    def stop(self, timeout_s: float = 5.0) -> None:
        """Shut down the background uvicorn server cleanly and unregister it."""
        with _REGISTRY_LOCK:
            existing = _ACTIVE_SERVERS.get((self.host, self.port))
            if existing is self:
                _ACTIVE_SERVERS.pop((self.host, self.port), None)

        if not self._owns_thread:
            return

        if self._uvicorn_server is not None:
            self._uvicorn_server.should_exit = True
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=timeout_s)
        self._uvicorn_server = None
        self._thread = None


def _external_health_check(host: str, port: int) -> bool:
    try:
        resp = httpx.get(f"http://{host}:{port}/health", timeout=0.4)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


def start_mock_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    reset_state: bool = True,
) -> MockEnterpriseServer:
    """Idempotently start (or reuse) the mock enterprise FastAPI server from Jupyter or Python."""
    key = (host, port)
    with _REGISTRY_LOCK:
        existing = _ACTIVE_SERVERS.get(key)
        if existing is not None and existing.is_running():
            if reset_state:
                existing.reset_metrics()
                existing.reset_faults()
            return existing

        if _external_health_check(host, port):
            client_handle = MockEnterpriseServer(host=host, port=port, owns_thread=False)
            _ACTIVE_SERVERS[key] = client_handle
            if reset_state:
                client_handle.reset_metrics()
                client_handle.reset_faults()
            return client_handle

        handle = MockEnterpriseServer(host=host, port=port, owns_thread=True)
        handle.start()
        _ACTIVE_SERVERS[key] = handle
        return handle

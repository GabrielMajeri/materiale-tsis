"""Standalone CLI entry point for running the mock enterprise FastAPI server."""

from __future__ import annotations

import argparse

import uvicorn

from supply_chain_demo.server.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Supply Chain mock enterprise server.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    args = parser.parse_args()
    uvicorn.run(create_app(), host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()

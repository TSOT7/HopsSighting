"""Serve the HopsSighting frontend with Python's built-in HTTP server.

No Node, no Deno — if you can run the backend, you can run this.

Usage:
    python3 serve.py          # serves ./src on http://localhost:8000
    python3 serve.py 9000     # pick a different port
"""
import functools
import http.server
import socketserver
import sys
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
ROOT = Path(__file__).parent / "src"

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))

with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
    print(f"HopsSighting frontend serving {ROOT} at http://localhost:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")

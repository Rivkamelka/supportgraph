"""Vercel entry point.

Vercel's Python runtime looks for an ASGI-compatible `app` object in files
under api/*.py and serves it directly -- no extra adapter needed for
FastAPI. All routing is otherwise unchanged; see app/main.py for the real
application. vercel.json rewrites every request to this file.
"""

from app.main import app  # noqa: F401

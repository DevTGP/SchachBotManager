"""Entry point for gunicorn: gunicorn sbm_api.wsgi:app."""

from sbm_api.app import create_app

app = create_app()

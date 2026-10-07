"""Access to what create_app set up, from inside a request."""

from datetime import datetime

from flask import current_app
from pymongo.database import Database


def db() -> Database:
    return current_app.extensions["sbm"]["db"]


def now() -> datetime:
    return current_app.extensions["sbm"]["now"]()


def public_url() -> str:
    return current_app.extensions["sbm"]["public_url"]

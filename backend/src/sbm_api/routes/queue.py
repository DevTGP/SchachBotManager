"""GET /queue: running and waiting matches with estimated times (E20)."""

from flask import Blueprint

from sbm_api import context
from sbm_api.queue_view import queue_view

blueprint = Blueprint("queue", __name__)


@blueprint.get("/queue")
def get_queue():
    return queue_view(context.db(), context.now())

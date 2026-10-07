from datetime import datetime
from pathlib import Path

import pytest
from flask.testing import FlaskClient
from openapi_core import Config, OpenAPI
from openapi_core.contrib.werkzeug import WerkzeugOpenAPIRequest, WerkzeugOpenAPIResponse
from sbm.referee import STANDARD_FEN
from sbm_store import bots
from sbm_store.enqueue import enqueue_match
from sbm_store.migrate import migrate

from sbm_api.app import create_app

from stored_games import BLITZ, NOW, SITE

SPEC = Path(__file__).resolve().parents[2] / "spec" / "web" / "openapi.json"


@pytest.fixture(scope="session")
def openapi() -> OpenAPI:
    # openapi-core only decodes the media types it knows; PGN is text.
    pgn_as_text = {"application/x-chess-pgn": lambda data: data.decode("utf-8")}
    config = Config(extra_media_type_deserializers=pgn_as_text)
    return OpenAPI.from_file_path(str(SPEC), config=config)


@pytest.fixture
def reference_bots(db) -> tuple[dict, dict]:
    migrate(db)
    return bots.by_name(db, "Random"), bots.by_name(db, "Material")


@pytest.fixture
def client(db, openapi):
    """A test client whose every response must match the OpenAPI document."""
    app = create_app(db, now=lambda: NOW, public_url=SITE)
    app.testing = True

    class CheckedClient(FlaskClient):
        def open(self, *args, **kwargs):
            response = super().open(*args, **kwargs)
            openapi.validate_response(
                WerkzeugOpenAPIRequest(response.request), WerkzeugOpenAPIResponse(response)
            )
            return response

    app.test_client_class = CheckedClient
    return app.test_client()


@pytest.fixture
def enqueue(db, reference_bots):
    def enqueue(*, now: datetime = NOW, priority: int = 100, start_fen: str = STANDARD_FEN):
        white, black = reference_bots
        return enqueue_match(
            db, white, black, BLITZ, start_fen=start_fen, now=now, priority=priority
        )

    return enqueue

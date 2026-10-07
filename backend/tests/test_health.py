from pymongo import MongoClient

from sbm_api.app import create_app


def test_health_reports_ok(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_health_without_database_is_unavailable():
    unreachable = MongoClient("mongodb://127.0.0.1:1", serverSelectionTimeoutMS=100)
    app = create_app(unreachable["sbm"])
    response = app.test_client().get("/api/v1/health")
    assert response.status_code == 503
    assert response.json["code"] == "unavailable"


def test_unknown_path_is_not_found(db):
    response = create_app(db).test_client().get("/api/v1/nothing")
    assert response.status_code == 404
    assert response.json["code"] == "not_found"


def test_wrong_method_is_not_found(db):
    response = create_app(db).test_client().post("/api/v1/health")
    assert response.status_code == 405
    assert response.json["code"] == "not_found"


def test_unexpected_error_is_internal(db):
    class BrokenDatabase:
        def command(self, name):
            raise RuntimeError("boom")

    response = create_app(BrokenDatabase()).test_client().get("/api/v1/health")
    assert response.status_code == 500
    assert response.json == {"code": "internal", "message": "internal error"}

from sbm_store import queue_settings


def test_defaults_without_a_document(db):
    assert queue_settings.get(db) == queue_settings.QueueSettings(paused=False, parallelism=1)


def test_pause_and_resume(db):
    queue_settings.set_paused(db, True)
    assert queue_settings.get(db).paused
    queue_settings.set_paused(db, False)
    assert not queue_settings.get(db).paused

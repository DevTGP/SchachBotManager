import pytest

from sbm_store import account_settings, coder_settings, estimate_settings, rating_settings
from sbm_store.rating_rule import DEFAULT, RatingRule

GROUPS = [
    (coder_settings, coder_settings.CoderSettings),
    (account_settings, account_settings.AccountSettings),
    (estimate_settings, estimate_settings.EstimateSettings),
    (rating_settings, RatingRule),
]


@pytest.mark.parametrize(("module", "kind"), GROUPS)
def test_defaults_without_a_document(db, module, kind):
    assert module.get(db) == kind()


@pytest.mark.parametrize(("module", "kind"), GROUPS)
def test_defaults_lie_within_the_limits(module, kind):
    defaults = kind()
    assert set(module.LIMITS) == set(vars(defaults))
    for name, (low, high) in module.LIMITS.items():
        assert low <= getattr(defaults, name) <= high
    assert module.problem(defaults) is None


def test_saved_values_come_back_and_missing_ones_keep_their_default(db):
    coder_settings.save(db, coder_settings.CoderSettings(games_per_day=3, priority=10))
    assert coder_settings.get(db) == coder_settings.CoderSettings(games_per_day=3, priority=10)

    db["settings"].update_one({"_id": "estimate"}, {"$set": {"recent_games": 5}}, upsert=True)
    assert estimate_settings.get(db) == estimate_settings.EstimateSettings(recent_games=5)


def test_groups_keep_separate_documents(db):
    account_settings.save(db, account_settings.AccountSettings(login_failures=9))
    rating_settings.save(db, RatingRule(start=1500))
    assert account_settings.get(db).login_failures == 9
    assert rating_settings.get(db).start == 1500
    assert coder_settings.get(db) == coder_settings.CoderSettings()


def test_invite_days_may_not_exceed_the_maximum():
    settings = account_settings.AccountSettings(invite_days=31, invite_max_days=30)
    assert account_settings.problem(settings) == "invite_days"


@pytest.mark.parametrize(
    ("rule", "field"),
    [
        (RatingRule(min_win=60), "min_win"),
        (RatingRule(max_win=40), "max_win"),
        (RatingRule(min_win=50, max_win=50), None),
    ],
)
def test_the_win_bounds_frame_the_base(rule, field):
    assert rating_settings.problem(rule) == field


def test_the_default_rule_is_the_one_of_e103():
    expected = RatingRule(start=2500, base=50, step=20, max_win=100, min_win=1, max_draw=50)
    assert expected == DEFAULT

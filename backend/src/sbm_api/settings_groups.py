"""The groups of settings an admin changes on /admin/settings (E154).

Each group is one document in the settings collection with a module that knows its type, its
ranges and the rule between its fields.
"""

from dataclasses import dataclass
from types import ModuleType

from sbm_store import account_settings, coder_settings, estimate_settings, rating_settings
from sbm_store.account_settings import AccountSettings
from sbm_store.coder_settings import CoderSettings
from sbm_store.estimate_settings import EstimateSettings
from sbm_store.rating_rule import RatingRule


@dataclass(frozen=True)
class Group:
    name: str  # in the path, the audit action and the schema AdminSettings
    module: ModuleType
    kind: type


GROUPS = (
    Group("coders", coder_settings, CoderSettings),
    Group("accounts", account_settings, AccountSettings),
    Group("rating", rating_settings, RatingRule),
    Group("estimate", estimate_settings, EstimateSettings),
)

# Why a field returned by problem() does not fit the others.
PROBLEMS = {
    "invite_days": "must not exceed invite_max_days",
    "min_win": "must not exceed base",
    "max_win": "must not be below base",
}

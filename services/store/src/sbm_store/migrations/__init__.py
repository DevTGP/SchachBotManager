"""Versioned migrations in the order they run; each one runs once per database."""

from sbm_store.migrations import (
    m0001_indexes,
    m0002_reference_bots,
    m0003_accounts,
    m0004_uploads,
    m0005_disciplines,
    m0006_ratings,
    m0110_play_origin,
    m0111_api_tokens,
)

MIGRATIONS = [
    ("0001_indexes", m0001_indexes.apply),
    ("0002_reference_bots", m0002_reference_bots.apply),
    ("0003_accounts", m0003_accounts.apply),
    ("0004_uploads", m0004_uploads.apply),
    ("0005_disciplines", m0005_disciplines.apply),
    ("0006_ratings", m0006_ratings.apply),
    # M7 numbers its migrations from 0110 on, beside M4 (E110).
    ("0110_play_origin", m0110_play_origin.apply),
    ("0111_api_tokens", m0111_api_tokens.apply),
]

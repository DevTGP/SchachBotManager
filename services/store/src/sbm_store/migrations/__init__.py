"""Versioned migrations in the order they run; each one runs once per database."""

from sbm_store.migrations import m0001_indexes, m0002_reference_bots

MIGRATIONS = [
    ("0001_indexes", m0001_indexes.apply),
    ("0002_reference_bots", m0002_reference_bots.apply),
]

"""Collection names (datenmodell.md)."""

BOTS = "bots"
MATCHES = "matches"
JOBS = "jobs"
SETTINGS = "settings"
MIGRATIONS = "schema_migrations"
USERS = "users"
SESSIONS = "sessions"
INVITES = "invites"
PASSWORD_RESETS = "password_resets"
AUDIT_LOG = "audit_log"
RATE_LIMITS = "rate_limits"
VERIFICATION_REPORTS = "verification_reports"
DISCIPLINES = "disciplines"
# Personal tokens of coders for remote bots (E116).
API_TOKENS = "api_tokens"
# GridFS bucket for the uploaded files of bots (E82): bot_files.files and bot_files.chunks.
BOT_FILES = "bot_files"
# Leagues, their seasons and the registrations of bots (E131, E132, E136).
LEAGUES = "leagues"
SEASONS = "seasons"
REGISTRATIONS = "registrations"
# Tournaments and their editions (E172, E173); registrations hold both kinds of targets.
TOURNAMENTS = "tournaments"
EDITIONS = "editions"

"""Entry point sbm-invite: an invite link from the command line, e.g. for the first admin (E83).

On the server: docker compose -f deploy/compose.yaml run --rm api sbm-invite --role admin
"""

import argparse
import os
import sys
from datetime import UTC, datetime, timedelta

from sbm_store import audit, invites, users
from sbm_store.connection import database_from_env

from sbm_api.app import PUBLIC_URL_VARIABLE
from sbm_api.links import INVITE_PAGE, one_time_link
from sbm_api.routes.admin_invites import DEFAULT_VALID_DAYS, MAX_VALID_DAYS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sbm-invite",
        description="Print a one-time invite link; database from SBM_MONGO_URI, "
        "address from SBM_PUBLIC_URL.",
    )
    parser.add_argument("--role", choices=users.ROLES, default=users.CODER)
    parser.add_argument(
        "--valid-days",
        type=int,
        default=DEFAULT_VALID_DAYS,
        help=f"1 to {MAX_VALID_DAYS} (default: {DEFAULT_VALID_DAYS})",
    )
    return parser


def main(argv: list[str] | None = None, environ: dict[str, str] = os.environ) -> int:
    args = build_parser().parse_args(argv)
    if not 1 <= args.valid_days <= MAX_VALID_DAYS:
        print(f"sbm-invite: --valid-days must be from 1 to {MAX_VALID_DAYS}", file=sys.stderr)
        return 2
    public_url = environ.get(PUBLIC_URL_VARIABLE)
    if not public_url:
        print(f"sbm-invite: {PUBLIC_URL_VARIABLE} is not set", file=sys.stderr)
        return 2
    try:
        db = database_from_env(environ)
    except RuntimeError as error:
        print(f"sbm-invite: {error}", file=sys.stderr)
        return 2
    now = datetime.now(UTC)
    invite, token = invites.create(
        db,
        args.role,
        created_by=None,
        created_by_name=None,
        now=now,
        expires_at=now + timedelta(days=args.valid_days),
    )
    audit.record(
        db,
        actor_id=None,
        actor=audit.CLI,
        action="invite.create",
        target=invite["_id"],
        details={"role": args.role, "valid_days": args.valid_days},
        now=now,
    )
    print(one_time_link(public_url, INVITE_PAGE, token))
    return 0


if __name__ == "__main__":
    sys.exit(main())

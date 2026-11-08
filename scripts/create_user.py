"""Create a BidPilot user (and optionally its company) directly in MongoDB.

    python scripts/create_user.py admin@acme.gr --company-id acme --role admin --company-name "Acme"
    python scripts/create_user.py guest@bidpilot.local --company-id demo-co --role viewer --demo

The password is read from BIDPILOT_PASSWORD or prompted, never passed as an argument.
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.exceptions import NotFoundError  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.company import CompanyProfile  # noqa: E402
from app.models.user import User  # noqa: E402
from app.repositories.companies import get_company, upsert_company  # noqa: E402
from app.repositories.mongo import close_client  # noqa: E402
from app.repositories.users import create_user, ensure_user_indexes, get_user_by_email  # noqa: E402


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("--company-id", required=True)
    parser.add_argument("--role", choices=["admin", "member", "viewer"], default="viewer")
    parser.add_argument("--demo", action="store_true", help="public demo account (daily quota)")
    parser.add_argument("--company-name", help="create the company if it does not exist")
    args = parser.parse_args()

    password = os.environ.get("BIDPILOT_PASSWORD") or getpass.getpass("Password: ")
    if len(password) < 10:
        print("password must be at least 10 characters", file=sys.stderr)
        return 1

    try:
        await ensure_user_indexes()
        if await get_user_by_email(args.email):
            print(f"user {args.email} already exists", file=sys.stderr)
            return 1
        try:
            await get_company(args.company_id)
        except NotFoundError:
            if not args.company_name:
                print(f"company {args.company_id} not found, pass --company-name", file=sys.stderr)
                return 1
            await upsert_company(CompanyProfile(id=args.company_id, name=args.company_name))
            print(f"created company {args.company_id}")

        user = await create_user(
            User(
                email=args.email,
                hashed_password=hash_password(password),
                company_id=args.company_id,
                role=args.role,
                is_demo=args.demo,
            )
        )
        print(
            f"created user {user.email} ({user.role}{', demo' if user.is_demo else ''}) id={user.id}"
        )
        return 0
    finally:
        await close_client()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

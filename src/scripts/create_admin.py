#!/usr/bin/env python
"""Create an admin user for the marketplace.

Usage:
    python -m src.scripts.create_admin --email EMAIL [--password PASSWORD] [--name NAME]

Example:
    # Create a new admin user
    python -m src.scripts.create_admin --email admin@example.com --password securepassword --name "Admin User"

    # Upgrade existing user to admin
    python -m src.scripts.create_admin --email existing@example.com
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add the src directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from business.user.models import User
from business.user.service import get_password_hash
from core.db import init_db


async def create_admin_user(email: str, password: str = None, name: str = None):
    """Create an admin user with the given credentials or upgrade existing user."""
    # Initialize database connection
    await init_db()

    # Check if user already exists
    existing_user = await User.find_one(User.email == email.lower())
    if existing_user:
        if existing_user.is_admin:
            print(f"Admin user {email} already exists.")
            return
        else:
            # Update existing user to be an admin
            existing_user.is_admin = True
            await existing_user.save()
            print(f"User {email} has been updated to have admin privileges.")
            return

    # If only email is provided but user doesn't exist
    if password is None or name is None:
        print(f"User {email} does not exist. Please provide password and name to create a new admin user.")
        return

    # Create new admin user
    password_hash = get_password_hash(password)
    admin_user = User(
        name=name,
        email=email.lower(),
        password_hash=password_hash,
        is_admin=True,
    )
    await admin_user.insert()
    print(f"Created admin user: {email}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or upgrade an admin user")
    parser.add_argument("--email", required=True, help="Email address of the user")
    parser.add_argument("--password", help="Password for new admin user (not needed for upgrading existing users)")
    parser.add_argument("--name", help="Name for new admin user (not needed for upgrading existing users)")

    args = parser.parse_args()

    asyncio.run(create_admin_user(args.email, args.password, args.name))

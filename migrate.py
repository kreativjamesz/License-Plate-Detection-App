#!/usr/bin/env python3
"""
Database Migration CLI - Laravel style

Usage:
    python migrate.py migrate    # Run migrations
    python migrate.py seed       # Run seeders  
    python migrate.py fresh      # Drop, migrate, and seed
"""

import sys
from app.database.database_service import DatabaseService


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    try:
        if command == "migrate":
            print("🚀 Running database migration...")
            DatabaseService.migrate()

        elif command == "seed":
            print("🌱 Running database seeders...")
            DatabaseService.seed()

        elif command == "fresh":
            print("✨ Running fresh migration with seeders...")
            DatabaseService.fresh()

        else:
            print(f"❌ Unknown command: {command}")
            print(__doc__)

    except Exception as e:
        print(f"💥 Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

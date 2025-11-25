#!/usr/bin/env python3
"""
Simple database migration to add last_message column
"""
import sqlite3
import sys

def migrate():
    """Add last_message column to games table if it doesn't exist"""
    db_path = "puzzle_game.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column exists
        cursor.execute("PRAGMA table_info(games)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'last_message' not in columns:
            print("Adding last_message column to games table...")
            cursor.execute("ALTER TABLE games ADD COLUMN last_message TEXT")
            conn.commit()
            print("✓ Migration complete!")
        else:
            print("✓ Column already exists, no migration needed")

        conn.close()
        return True

    except Exception as e:
        print(f"✗ Migration failed: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Initialize the Bitarr database.
"""
from bitarr.db.init_db import init_db

if __name__ == "__main__":
    db_path = init_db()
    print(f"Database initialized at: {db_path}")

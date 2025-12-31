
import os
import sys
# Must load .env before importing database module to pick up DATABASE_URL
from dotenv import load_dotenv
load_dotenv()

import database
import datetime
from sqlalchemy import text

def check_full_cycle():
    print("=== FULL CYCLE CHECK ===")
    
    # 1. Print Database Connection Info
    print(f"Dialect: {database.engine.dialect.name}")
    print(f"DB URL (masked): {str(database.engine.url).replace(':', '***').replace('@', '***')}")
    if database.engine.dialect.name == 'sqlite':
        db_path = database.engine.url.database
        print(f"SQLite File Path: {os.path.abspath(db_path) if db_path else 'Memory'}")
        print("WARNING: Connected to local SQLite, not Remote Postgres!")
    else:
        print("Connected to Remote Database (PostgreSQL)")

    # 2. Insert Test Record
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    test_code = f"TEST_CODE_{timestamp}"
    
    print(f"\n[WRITE] Attempting to insert record with code: {test_code}")
    try:
        success = database.add_history_entry(
            code=test_code,
            result="Test Result",
            passenger_info="TEST PAX",
            route_info="TEST-ROUTE",
            timestamp=timestamp,
            cost="100",
            price="200",
            data_json="{}"
        )
        print(f"[WRITE] Result: {success}")
    except Exception as e:
        print(f"[WRITE] FAILED: {e}")
        return

    # 3. Read Back Immediately using get_history_entries (same function UI uses)
    print(f"\n[READ] Attempting to read back history...")
    try:
        history = database.get_history_entries(limit=5)
        found = False
        for entry in history:
            print(f" - Found Entry ID: {entry.get('id')}, Code: {entry.get('code')}, TS: {entry.get('timestamp')}")
            if entry.get('code') == test_code:
                found = True
        
        if found:
            print("\n[SUCCESS] Record verified! The database is working correctly.")
        else:
            print("\n[FAILURE] Record NOT found in history list. Potential timezone/ordering issue or transaction rollback.")
            
    except Exception as e:
        print(f"[READ] FAILED: {e}")

if __name__ == "__main__":
    check_full_cycle()

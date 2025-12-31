
import os
import sys
# Must load .env before importing database module
from dotenv import load_dotenv
load_dotenv()

import database
from sqlalchemy import text

def fix_schema():
    print("Checking database schema...")
    print(f"Dialect: {database.engine.dialect.name}")
    
    # Define columns to check/add
    columns = ["data_json", "cost", "price"]
    
    for col in columns:
        print(f"--- Checking column: {col} ---")
        try:
            # Use separate connection for checking to avoid transaction state issues
            with database.engine.connect() as conn:
                try:
                    conn.execute(text(f"SELECT {col} FROM history LIMIT 1"))
                    print(f"SUCCESS: '{col}' column exists.")
                except Exception:
                    print(f"WARNING: '{col}' column missing or query failed. Attempting to add...")
                    
            # Use separate transaction for modification
            # IMPORTANT: For Postgres, we must start a fresh transaction block
            with database.engine.begin() as conn:
                try:
                    if database.engine.dialect.name == "postgresql":
                        conn.execute(text(f"ALTER TABLE history ADD COLUMN IF NOT EXISTS {col} TEXT"))
                    else:
                        conn.execute(text(f"ALTER TABLE history ADD COLUMN {col} TEXT"))
                    print(f"Executed ADD COLUMN for {col}")
                except Exception as e:
                    print(f"Add column {col} failed: {e}")
                    
        except Exception as e:
             print(f"Outer error checking/adding {col}: {e}")

    print("Schema verification complete.")

if __name__ == "__main__":
    fix_schema()

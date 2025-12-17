import os
import json
import database

def migrate():
    print("Starting migration to SQLite...")
    
    # 1. Migrate Airports (fly.txt)
    fly_path = "fly.txt"
    if os.path.exists(fly_path):
        count = 0
        with open(fly_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) >= 2:
                    code = parts[0].strip().upper()
                    name = parts[1].strip()
                    database.upsert_airport(code, name)
                    count += 1
        print(f"Migrated {count} airports.")
    
    # 2. Migrate History (history.json)
    hist_path = "history.json"
    if os.path.exists(hist_path):
        count = 0
        try:
            with open(hist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Reverse to insert oldest first so IDs are sequential? 
                # Actually insertion order matters for 'ORDER BY id DESC'.
                # history.json is "Newest First" (index 0 is newest).
                # So we should insert from end to start to keep ID order logical, 
                # or just insert and let timestamp sort it (our query sorts by ID).
                # If we insert newest first, ID 1 will be Newest. 
                # Query: ORDER BY id DESC -> ID 1 comes last.
                # So newest (ID 1) shows at bottom? Incorrect.
                # If we insert Newest (A), then Older (B). ID(A)=1, ID(B)=2.
                # ORDER BY ID DESC -> B, A.
                # So we want Newest to have Highest ID.
                # history.json is [Newest, Older, Oldest].
                # We should insert Oldest -> Newest.
                
                for item in reversed(data):
                    # Use database module's function with explicit timestamp
                    database.add_history_entry(
                        item.get('code', ''),
                        item.get('result', ''),
                        item.get('passenger_info', ''),
                        item.get('route_info', ''),
                        timestamp=item.get('timestamp', '')
                    )
                    count += 1
            print(f"Migrated {count} history entries.")
        except Exception as e:
            print(f"Error migrating history: {e}")

if __name__ == "__main__":
    migrate()

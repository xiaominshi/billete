
import database
import datetime
from sqlalchemy import text

def debug_insert():
    print("--- START DEBUG INSERT ---")
    
    # 1. The problematic raw code
    raw_code = """1.SHAO/XUEPING   2.XU/JINSONG 
   3  3U3804 N 13MAR 5 MADTFU HK2       1  1105 0545+1 *1A/E* 
   4  3U6901 B 14MAR 6 TFUWNZ HK2       2  0920 1135   *1A/E* 
   5  3U6904 B 12APR 7 WNZTFU HK2       2  2005 2250   *1A/E* 
   6  3U3803 R 13APR 1 TFUMAD HK2       1  0140 0850   *1A/E*"""

    # 2. Simulate sanitized code (server.py logic)
    safe_code = raw_code.replace('\x00', '')
    
    print(f"Raw code length: {len(raw_code)}")
    print(f"Safe code length: {len(safe_code)}")
    
    # 3. Simulate other data
    result_text = "Debug Result Text"
    pax_info = "SHAO/XUEPING, XU/JINSONG"
    route_info = "MAD-WNZ"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 4. Call add_history_entry directly
    print("Attempting database.add_history_entry...")
    try:
        success = database.add_history_entry(
            code=safe_code,
            result=result_text,
            passenger_info=pax_info,
            route_info=route_info,
            timestamp=timestamp,
            cost="0",
            price="0",
            data_json="{}"
        )
        print(f"add_history_entry returned: {success}")
    except Exception as e:
        print(f"add_history_entry raised exception: {e}")
        import traceback
        traceback.print_exc()

    # 5. Verify insertion
    print("Verifying insertion...")
    try:
        with database.engine.connect() as conn:
            # Check if our entry exists (by timestamp match for precision)
            row = conn.execute(
                text("SELECT id, code, passenger_info FROM history WHERE timestamp = :ts"), 
                {"ts": timestamp}
            ).fetchone()
            
            if row:
                print(f"SUCCESS: Found record! ID: {row.id}")
                print(f"Saved Code starts with: {row.code[:20]}...")
            else:
                print("FAILURE: Record not found in SELECT query.")
                
            # Check total count
            count = conn.execute(text("SELECT COUNT(*) FROM history")).scalar()
            print(f"Total rows in history: {count}")
            
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    debug_insert()

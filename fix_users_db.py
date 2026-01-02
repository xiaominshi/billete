import sqlite3
import os

db_path = "billete.db"
if not os.path.exists(db_path):
    if os.path.exists("billetepython/billete.db"):
        db_path = "billetepython/billete.db"

print(f"Fixing DB at: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Check users table columns
print("Checking users table schema...")
try:
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Current columns: {columns}")
    
    if "is_admin" not in columns:
        print("Adding is_admin column...")
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
            conn.commit()
            print("Done.")
        except Exception as e:
            print(f"Failed to alter users: {e}")
            
            # If ALTER fails (old sqlite), recreate table?
            # Or maybe the table was created wrong initially.
            
except Exception as e:
    print(f"Error checking schema: {e}")

# 2. Check if admin exists
try:
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if cursor.fetchone():
        print("Admin user exists.")
        # Update admin to be admin
        cursor.execute("UPDATE users SET is_admin=1 WHERE username='admin'")
        conn.commit()
        print("Admin privileges ensured.")
    else:
        print("Admin user does not exist (will be created by app).")
        
except Exception as e:
    print(f"Error checking admin: {e}")

conn.close()

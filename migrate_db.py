import sqlite3
import os

db_path = "billete.db"
if not os.path.exists(db_path):
    if os.path.exists("billetepython/billete.db"):
        db_path = "billetepython/billete.db"

print(f"Migrating database at: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. Add user_id to airports
try:
    print("Checking airports table...")
    cursor.execute("SELECT user_id FROM airports LIMIT 1")
    print(" - user_id exists in airports.")
except sqlite3.OperationalError:
    print(" - Adding user_id column to airports...")
    try:
        cursor.execute("ALTER TABLE airports ADD COLUMN user_id INTEGER")
        conn.commit()
        print(" - Done.")
    except Exception as e:
        print(f" - Failed: {e}")

# 2. Add user_id to history
try:
    print("Checking history table...")
    cursor.execute("SELECT user_id FROM history LIMIT 1")
    print(" - user_id exists in history.")
except sqlite3.OperationalError:
    print(" - Adding user_id column to history...")
    try:
        cursor.execute("ALTER TABLE history ADD COLUMN user_id INTEGER")
        conn.commit()
        print(" - Done.")
    except Exception as e:
        print(f" - Failed: {e}")

# 3. Create users table if not exists
try:
    print("Checking users table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username VARCHAR NOT NULL UNIQUE,
            password_hash VARCHAR NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    print(" - Users table ensured.")
except Exception as e:
    print(f" - Failed to create users table: {e}")

# 4. Ensure admin user
try:
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        print("Creating default admin user...")
        from werkzeug.security import generate_password_hash
        p_hash = generate_password_hash("xiaominshi")
        cursor.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)", ("admin", p_hash, 1))
        conn.commit()
        print(" - Admin user created.")
    else:
        print(" - Admin user already exists.")
except Exception as e:
    print(f" - Failed to check/create admin: {e}")

conn.close()
print("Migration completed.")

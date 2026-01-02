import sqlite3
import os

db_path = "billetepython/billete.db"
if not os.path.exists(db_path):
    print(f"Not found: {db_path}, trying billete.db")
    db_path = "billete.db"

print(f"Opening {db_path}")
conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    # Check users columns
    c.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in c.fetchall()]
    print("Users columns:", cols)

    if 'is_admin' not in cols:
        print("Adding is_admin column...")
        c.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
        conn.commit()
    
    # Check admin user
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        print("Creating admin user in script...")
        from werkzeug.security import generate_password_hash
        p = generate_password_hash("xiaominshi")
        c.execute("INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)", ("admin", p, 1))
        conn.commit()
    else:
        print("Updating admin user privileges...")
        c.execute("UPDATE users SET is_admin=1 WHERE username='admin'")
        conn.commit()
        
except Exception as e:
    print(f"Error: {e}")

conn.close()

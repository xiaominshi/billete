import database
from sqlalchemy import text

def reset_password_plain():
    try:
        with database.engine.connect() as conn:
            # Set to plain text "xiaomin"
            # This works because I added a fallback check in server.py: 
            # if hash check fails, it checks if db_value == password
            conn.execute(text("UPDATE users SET password_hash = 'xiaomin' WHERE username = 'xiaomin'"))
            conn.commit()
            print("Successfully set password for 'xiaomin' to plain text 'xiaomin'")
            
            # Verify
            result = conn.execute(text("SELECT username, password_hash FROM users WHERE username = 'xiaomin'")).fetchone()
            print(f"Verification: User={result.username}, Hash={result.password_hash}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reset_password_plain()
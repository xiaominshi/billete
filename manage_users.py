import database
from werkzeug.security import generate_password_hash
import sys

def add_user(username, password):
    if database.get_user_by_username(username):
        print(f"Error: User '{username}' already exists.")
        return False
    
    password_hash = generate_password_hash(password)
    if database.create_user(username, password_hash):
        print(f"Success: User '{username}' created.")
        return True
    else:
        print("Error: Failed to create user.")
        return False

def list_users():
    with database.engine.connect() as conn:
        result = conn.execute(database.text("SELECT id, username FROM users"))
        print("\nExisting Users:")
        print("-" * 20)
        for row in result:
            print(f"ID: {row.id} | Username: {row.username}")
        print("-" * 20)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        add_user(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2 and sys.argv[1] == "list":
        list_users()
    else:
        print("Usage:")
        print("  python manage_users.py <username> <password>  # Add new user")
        print("  python manage_users.py list                   # List all users")

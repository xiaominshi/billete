import os
import datetime
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer
from sqlalchemy.pool import NullPool

# Detect environment: Render uses DATABASE_URL
# Handle "postgres://" fix for SQLAlchemy 1.4+
db_url = os.getenv("DATABASE_URL", "sqlite:///billete.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)
metadata = MetaData()

# Define tables using SQLAlchemy Core for cross-db compatibility
airports_table = Table('airports', metadata,
    Column('code', String, primary_key=True),
    Column('name', String, nullable=False)
)

history_table = Table('history', metadata,
    Column('id', Integer, primary_key=True),
    Column('timestamp', String),
    Column('code', String),
    Column('result', String),
    Column('passenger_info', String),
    Column('route_info', String)
)

def init_db():
    metadata.create_all(engine)

def create_user(username, password_hash):
    try:
        with engine.connect() as conn:
            conn.execute(
                text("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)"),
                {"username": username, "password_hash": password_hash}
            )
            conn.commit()
            return True
    except Exception as e:
        print(f"Create User Error: {e}")
        return False

def get_user_by_username(username):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()
        if result:
            return {"id": result.id, "username": result.username, "password_hash": result.password_hash}
        return None

def get_user_by_id(user_id):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        ).fetchone()
        if result:
            return {"id": result.id, "username": result.username, "password_hash": result.password_hash}
        return None

def get_all_airports():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT code, name FROM airports"))
        return {row.code: row.name for row in result}

def upsert_airport(code, name):
    # Compatible UPSERT syntax for SQLite and PostgreSQL
    # Both support ON CONFLICT(code) DO UPDATE SET name=excluded.name
    # Note: SQLAlchemy 1.4+ Core doesn't abstract UPSERT fully cross-db in a simple way 
    # without using dialect-specific imports (sqlite.insert, postgresql.insert).
    # However, standard SQL "ON CONFLICT" works for both SQLite (since 3.24) and Postgres.
    
    # We use raw SQL for simplicity here to ensure the syntax matches both.
    sql = text('''
        INSERT INTO airports (code, name) VALUES (:code, :name)
        ON CONFLICT(code) DO UPDATE SET name=excluded.name
    ''')
    with engine.connect() as conn:
        conn.execute(sql, {"code": code.upper(), "name": name})
        conn.commit()

def delete_airport(code):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM airports WHERE code = :code"), {"code": code.upper()})
            conn.commit()
            return result.rowcount > 0
    except Exception as e:
        print(f"Delete Error: {e}")
        return False

def get_history_entries(limit=100):
    with engine.connect() as conn:
        # Use text() for query, but result columns are accessible by name
        result = conn.execute(
            text("SELECT * FROM history ORDER BY id DESC LIMIT :limit"),
            {"limit": limit}
        )
        history = []
        for row in result:
            # SQLAlchemy rows behave like named tuples
            history.append({
                "timestamp": row.timestamp,
                "code": row.code,
                "result": row.result,
                "passenger_info": row.passenger_info,
                "route_info": row.route_info
            })
        return history

def add_history_entry(code, result, passenger_info, route_info, timestamp=None):
    if not timestamp:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    with engine.connect() as conn:
        conn.execute(
            text('''
                INSERT INTO history (timestamp, code, result, passenger_info, route_info)
                VALUES (:timestamp, :code, :result, :passenger_info, :route_info)
            '''),
            {
                "timestamp": timestamp,
                "code": code,
                "result": result,
                "passenger_info": passenger_info,
                "route_info": route_info
            }
        )
        conn.commit()

def clear_history_entries():
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM history"))
        conn.commit()
    return True

def get_today_count():
    today_prefix = datetime.datetime.now().strftime("%Y-%m-%d") + "%"
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM history WHERE timestamp LIKE :prefix"),
            {"prefix": today_prefix}
        ).scalar()
        return result

# Initialize on import
init_db()

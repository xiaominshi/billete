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

def delete_old_history(days=30):
    """
    Delete history entries older than 'days' days.
    """
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("DELETE FROM history WHERE timestamp < :cutoff"),
                {"cutoff": cutoff_str}
            )
            conn.commit()
            print(f"Deleted {result.rowcount} old history entries (older than {days} days).")
            return result.rowcount
    except Exception as e:
        print(f"Failed to delete old history: {e}")
        return 0

def get_today_count():
    today_prefix = datetime.datetime.now().strftime("%Y-%m-%d") + "%"
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM history WHERE timestamp LIKE :prefix"),
            {"prefix": today_prefix}
        ).scalar()
        return result

def get_kpi_stats(days=7):
    """
    Get Key Performance Indicators (KPIs) for the last 'days' days.
    """
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    
    with engine.connect() as conn:
        # Total Searches
        total_searches = conn.execute(
            text("SELECT COUNT(*) FROM history WHERE timestamp >= :start"),
            {"start": start_str}
        ).scalar()
        
        # Calculate Pax Count (Rough approximation by counting 'Passenger' keywords or lines)
        # Doing this in Python for flexibility
        result = conn.execute(
            text("SELECT passenger_info FROM history WHERE timestamp >= :start"),
            {"start": start_str}
        )
        
        total_pax = 0
        for row in result:
            p_info = row.passenger_info or ""
            # Simple heuristic: count newlines + 1 (if not empty) or count explicit "Passenger" word
            if p_info:
                # Assuming standard format "Passenger 1: ... \n Passenger 2: ..."
                # Or user might paste just names.
                # Let's count non-empty lines as passengers
                lines = [l for l in p_info.split('\n') if l.strip()]
                total_pax += len(lines)
                
        avg_pax = round(total_pax / total_searches, 1) if total_searches > 0 else 0
        
        # Busiest Day
        # Using Python aggregation for simplicity cross-db
        daily_res = conn.execute(
            text("SELECT SUBSTR(timestamp, 1, 10) as dt, COUNT(*) as cnt FROM history WHERE timestamp >= :start GROUP BY dt ORDER BY cnt DESC LIMIT 1"),
            {"start": start_str}
        ).fetchone()
        
        busiest_day = daily_res.dt if daily_res else "N/A"
        
        return {
            "total_searches": total_searches,
            "total_pax": total_pax,
            "avg_pax": avg_pax,
            "busiest_day": busiest_day
        }

def get_daily_stats(days=7):
    """
    Get flight processing counts for the last 'days' days.
    """
    stats = []
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days-1)
    
    # Generate list of dates
    date_list = []
    curr = start_date
    while curr <= end_date:
        date_list.append(curr.strftime("%Y-%m-%d"))
        curr += datetime.timedelta(days=1)
        
    with engine.connect() as conn:
        sql = text('''
            SELECT SUBSTR(timestamp, 1, 10) as date_str, COUNT(*) as cnt 
            FROM history 
            WHERE timestamp >= :start_ts
            GROUP BY date_str
        ''')
        
        result = conn.execute(sql, {"start_ts": start_date.strftime("%Y-%m-%d")})
        db_counts = {row.date_str: row.cnt for row in result}
        
        for d in date_list:
            stats.append({"date": d, "count": db_counts.get(d, 0)})
            
    return stats

def get_top_routes(days=7, limit=5):
    """
    Get most frequent routes from history in the last 'days' days.
    """
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d")

    with engine.connect() as conn:
        result = conn.execute(
            text('''
                SELECT route_info, COUNT(*) as cnt 
                FROM history 
                WHERE route_info IS NOT NULL AND route_info != '' AND timestamp >= :start
                GROUP BY route_info 
                ORDER BY cnt DESC 
                LIMIT :limit
            '''),
            {"limit": limit, "start": start_str}
        )
        return [{"route": row.route_info, "count": row.cnt} for row in result]

def get_airline_stats(days=7, limit=1000):
    """
    Get airline distribution stats for the last 'days' days.
    """
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT code FROM history WHERE timestamp >= :start ORDER BY id DESC LIMIT :limit"),
            {"limit": limit, "start": start_str}
        )
        
        airline_counts = {}
        import re
        
        for row in result:
            raw_code = row.code
            matches = re.findall(r'([A-Z0-9]{2})\d{3,4}', raw_code)
            
            for airline in matches:
                if airline.isdigit(): continue
                airline_counts[airline] = airline_counts.get(airline, 0) + 1
                
        stats = [{"airline": k, "count": v} for k, v in airline_counts.items()]
        stats.sort(key=lambda x: x["count"], reverse=True)
        return stats[:10]

def get_hourly_stats(days=7, limit=1000):
    """
    Get activity by hour of day (0-23) for the last 'days' days.
    """
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT timestamp FROM history WHERE timestamp >= :start ORDER BY id DESC LIMIT :limit"),
            {"limit": limit, "start": start_str}
        )
        
        hours = {h: 0 for h in range(24)}
        
        for row in result:
            try:
                ts = row.timestamp
                if len(ts) >= 13:
                    h_str = ts[11:13]
                    h = int(h_str)
                    hours[h] += 1
            except:
                continue
                
        stats = [{"hour": f"{h:02d}:00", "count": hours[h]} for h in range(24)]
        return stats

def get_all_history_for_export():
    """Returns all history for CSV export"""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM history ORDER BY id DESC"))
        return [{
            "id": row.id,
            "timestamp": row.timestamp,
            "code": row.code,
            "passenger_info": row.passenger_info,
            "route_info": row.route_info
        } for row in result]

# Initialize on import
init_db()
# Auto-cleanup old history on startup (keep 30 days)
delete_old_history(30)

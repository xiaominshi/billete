import os
import datetime
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer
from sqlalchemy.pool import NullPool

# Detect environment: Render uses DATABASE_URL
# Handle "postgres://" fix for SQLAlchemy 1.4+
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "billete.db")
default_db_url = f"sqlite:///{db_path}"

db_url = os.getenv("DATABASE_URL", default_db_url)
# Normalize legacy scheme
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Use resilient settings for Neon/PostgreSQL
if db_url.startswith("postgresql://") or db_url.startswith("postgresql+"):
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        poolclass=NullPool
    )
else:
    # Increase timeout for SQLite to avoid "database is locked" errors
    engine = create_engine(db_url, connect_args={'timeout': 30})
metadata = MetaData()

# Define tables using SQLAlchemy Core for cross-db compatibility
users_table = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String, unique=True, nullable=False),
    Column('password_hash', String, nullable=False)
)

airports_table = Table('airports', metadata,
    Column('code', String, primary_key=True),
    Column('name', String, nullable=False)
)

history_table = Table('history', metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer), # Foreign key to users
    Column('timestamp', String),
    Column('code', String),
    Column('result', String),
    Column('passenger_info', String),
    Column('route_info', String),
    Column('cost', String), # Storing as String to avoid float precision issues or use Float/Numeric
    Column('price', String),
    Column('data_json', String) # JSON string
)

def init_db():
    metadata.create_all(engine)
    # Auto-migration for existing DBs
    dialect = engine.dialect.name
    
    # Define migration steps as separate operations
    columns_to_add = [
        ("cost", "TEXT"),
        ("price", "TEXT"),
        ("data_json", "TEXT"),
        ("user_id", "INTEGER")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            # Use engine.begin() to create a fresh transaction for EACH column
            with engine.begin() as conn:
                try:
                    if dialect == "postgresql":
                        conn.execute(text(f"ALTER TABLE history ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                    else:
                        # SQLite doesn't support IF NOT EXISTS in ADD COLUMN consistently across versions
                        conn.execute(text(f"ALTER TABLE history ADD COLUMN {col_name} {col_type}"))
                except Exception as e:
                    # Ignore error only if it's likely "column exists"
                    pass
        except Exception as outer_e:
            pass

    # Ensure admin user exists
    from werkzeug.security import generate_password_hash
    if not get_user_by_username('admin'):
        create_user('admin', generate_password_hash('admin'))
        print("Initialized admin user.")
    
    # Assign existing history to admin (user_id=1) if user_id is NULL
    try:
        with engine.begin() as conn:
            admin = get_user_by_username('admin')
            if admin:
                conn.execute(text("UPDATE history SET user_id = :uid WHERE user_id IS NULL"), {"uid": admin['id']})
    except Exception as e:
        print(f"Migration error assigning history to admin: {e}")


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

def get_all_users():
    """
    Get list of all users.
    """
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, username FROM users ORDER BY id ASC"))
        return [{"id": row.id, "username": row.username} for row in result]

def update_user_password(username, password_hash):
    """
    Update password for a specific user.
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("UPDATE users SET password_hash = :password_hash WHERE username = :username"),
                {"password_hash": password_hash, "username": username}
            )
            conn.commit()
            return result.rowcount > 0
    except Exception as e:
        print(f"Update Password Error: {e}")
        return False

def delete_user(username):
    """
    Delete a user by username.
    Prevents deleting 'admin'.
    """
    if username == 'admin':
        return False
        
    try:
        with engine.connect() as conn:
            # Optional: Delete history first? Or keep it?
            # Keeping history but setting user_id to NULL or keeping as is (orphan)
            # Let's set to NULL to preserve data stats
            # First get ID
            user = conn.execute(text("SELECT id FROM users WHERE username = :u"), {"u": username}).fetchone()
            if user:
                conn.execute(text("UPDATE history SET user_id = NULL WHERE user_id = :uid"), {"uid": user.id})
            
            result = conn.execute(
                text("DELETE FROM users WHERE username = :username"),
                {"username": username}
            )
            conn.commit()
            return result.rowcount > 0
    except Exception as e:
        print(f"Delete User Error: {e}")
        return False


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

def upsert_airports_batch(airports_list):
    """
    Batch insert/update airports in a single transaction.
    airports_list: list of dicts [{"code": "ABC", "name": "Airport Name"}, ...]
    """
    if not airports_list:
        return True

    sql = text('''
        INSERT INTO airports (code, name) VALUES (:code, :name)
        ON CONFLICT(code) DO UPDATE SET name=excluded.name
    ''')
    
    try:
        with engine.begin() as conn: # Begin transaction
            conn.execute(sql, airports_list)
        return True
    except Exception as e:
        print(f"Batch Upsert Error: {e}")
        return False

def delete_airport(code):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM airports WHERE code = :code"), {"code": code.upper()})
            conn.commit()
            return result.rowcount > 0
    except Exception as e:
        print(f"Delete Error: {e}")
        return False

def get_history_entries(limit=100, user_id=None):
    with engine.connect() as conn:
        # Use text() for query, but result columns are accessible by name
        sql = "SELECT * FROM history"
        params = {"limit": limit}
        
        if user_id:
            sql += " WHERE user_id = :user_id"
            params["user_id"] = user_id
            
        sql += " ORDER BY id DESC LIMIT :limit"
        
        result = conn.execute(text(sql), params)
        history = []
        for row in result:
            # SQLAlchemy rows behave like named tuples
            history.append({
                "id": row.id,
                "timestamp": row.timestamp,
                "code": row.code,
                "result": row.result,
                "passenger_info": row.passenger_info,
                "route_info": row.route_info,
                "cost": row.cost,
                "price": row.price,
                "data_json": row.data_json
            })
        return history

def add_history_entry(code, result, passenger_info, route_info, timestamp=None, cost=None, price=None, data_json=None, user_id=None):
    print(f"DEBUG: add_history_entry called. Code len: {len(code) if code else 0}, User: {user_id}")
    if not timestamp:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    # Pre-process None values to prevent SQL NULL injection errors
    vals = {
        "timestamp": timestamp,
        "code": code if code else "",
        "result": result if result else "",
        "passenger_info": passenger_info if passenger_info else "",
        "route_info": route_info if route_info else "",
        "cost": cost if cost is not None else "",
        "price": price if price is not None else "",
        "data_json": data_json if data_json is not None else "{}",
        "user_id": user_id
    }

    try:
        # Use engine.begin() for atomic transaction management
        with engine.begin() as conn:
            # 1. Deduplication (Enabled)
            # Delete old record with the same code to ensure only the latest version is stored
            # Scope deduplication to user? Or global? Probably user-scoped.
            if vals['code']:
                if user_id:
                    conn.execute(text("DELETE FROM history WHERE code = :code AND user_id = :user_id"), 
                                {"code": vals['code'], "user_id": user_id})
                else:
                     conn.execute(text("DELETE FROM history WHERE code = :code"), {"code": vals['code']})
            
            # 2. Insert new record
            conn.execute(
                text('''
                    INSERT INTO history (timestamp, code, result, passenger_info, route_info, cost, price, data_json, user_id)
                    VALUES (:timestamp, :code, :result, :passenger_info, :route_info, :cost, :price, :data_json, :user_id)
                '''),
                vals
            )
            # Transaction is automatically committed here
            print(f"DEBUG: Successfully added history for code length: {len(code) if code else 0}")
            return True
            
    except Exception as e:
        print(f"CRITICAL DB ERROR in add_history_entry: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_history_entry(history_id, cost=None, price=None, data_json=None):
    with engine.connect() as conn:
        updates = {}
        if cost is not None: updates['cost'] = cost
        if price is not None: updates['price'] = price
        if data_json is not None: updates['data_json'] = data_json
        
        if not updates: return False
        
        # Build set clause
        set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
        updates['id'] = history_id
        
        conn.execute(
            text(f"UPDATE history SET {set_clause} WHERE id = :id"),
            updates
        )
        conn.commit()
        return True

def delete_history_entry(history_id):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM history WHERE id = :id"), {"id": history_id})
            conn.commit()
            return result.rowcount > 0
    except Exception as e:
        print(f"Delete History Entry Error: {e}")
        return False

def clear_history_entries():
    try:
        with engine.connect() as conn:
            # Only delete NON-ISSUED and NO-FINANCIAL data
            sql = text('''
                DELETE FROM history 
                WHERE (code NOT LIKE '%FA PAX%')
                  AND (cost IS NULL OR cost = '' OR cost = '0')
                  AND (price IS NULL OR price = '' OR price = '0')
            ''')
            result = conn.execute(sql)
            conn.commit()
            return result.rowcount
    except Exception as e:
        print(f"Clear History Error: {e}")
        return 0

def delete_old_history(days=30):
    """
    Delete history entries older than 'days' days.
    """
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        with engine.connect() as conn:
            # Only delete if NOT issued (no 'FA PAX' in code) AND no financial data (cost/price empty)
            # Logic: timestamp < cutoff AND code NOT LIKE '%FA PAX%' AND (cost IS NULL OR cost = '') AND (price IS NULL OR price = '')
            # Note: Checking cost/price strings.
            
            sql = text('''
                DELETE FROM history 
                WHERE timestamp < :cutoff 
                  AND (code NOT LIKE '%FA PAX%')
                  AND (cost IS NULL OR cost = '' OR cost = '0')
                  AND (price IS NULL OR price = '' OR price = '0')
            ''')
            
            result = conn.execute(sql, {"cutoff": cutoff_str})
            conn.commit()
            print(f"Deleted {result.rowcount} old history entries (older than {days} days, non-issued only).")
            return result.rowcount
    except Exception as e:
        print(f"Failed to delete old history: {e}")
        return 0

def get_today_count(user_id=None):
    today_prefix = datetime.datetime.now().strftime("%Y-%m-%d") + "%"
    with engine.connect() as conn:
        sql = "SELECT COUNT(*) FROM history WHERE timestamp LIKE :prefix"
        params = {"prefix": today_prefix}
        if user_id:
            sql += " AND user_id = :user_id"
            params["user_id"] = user_id
            
        result = conn.execute(text(sql), params).scalar()
        return result

def get_kpi_stats(days=7, user_id=None):
    """
    Get Key Performance Indicators (KPIs) for the last 'days' days.
    Also calculates trend vs previous period.
    """
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=days)
    prev_start_date = start_date - datetime.timedelta(days=days)
    
    start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    prev_start_str = prev_start_date.strftime("%Y-%m-%d %H:%M:%S")
    prev_end_str = start_str # Previous period ends where current begins

    def calculate_metrics(s_date, e_date=None):
        with engine.connect() as conn:
            # Time filter
            if e_date:
                time_filter = "timestamp >= :start AND timestamp < :end"
                params = {"start": s_date, "end": e_date}
            else:
                time_filter = "timestamp >= :start"
                params = {"start": s_date}

            if user_id:
                time_filter += " AND user_id = :user_id"
                params["user_id"] = user_id

            # Total Searches
            total_searches = conn.execute(
                text(f"SELECT COUNT(*) FROM history WHERE {time_filter}"),
                params
            ).scalar()
            
            # Total Pax (Based on issued tickets "FA PAX")
            # We also need to calculate average group size for ticketed orders
            result = conn.execute(
                text(f"SELECT code FROM history WHERE {time_filter}"),
                params
            )
            
            total_pax = 0
            ticketed_orders = 0
            
            for row in result:
                code_text = row.code or ""
                # Count FA PAX occurrences to get number of tickets
                pax_count = code_text.count("FA PAX")
                
                if pax_count > 0:
                    total_pax += pax_count
                    ticketed_orders += 1
            
            # Average Pax (Average Group Size of Ticketed Orders)
            avg_pax = round(total_pax / ticketed_orders, 1) if ticketed_orders > 0 else 0
            
            return total_searches, total_pax, avg_pax

    # Current Period
    curr_searches, curr_pax, curr_avg = calculate_metrics(start_str)
    
    # Previous Period
    prev_searches, prev_pax, prev_avg = calculate_metrics(prev_start_str, start_str)
    
    # Calculate Changes (%)
    def calc_change(curr, prev):
        if prev == 0:
            return 100 if curr > 0 else 0
        return round(((curr - prev) / prev) * 100, 1)

    change_searches = calc_change(curr_searches, prev_searches)
    change_pax = calc_change(curr_pax, prev_pax)
    change_avg = calc_change(curr_avg, prev_avg)

    # Busiest Day (Current Period Only)
    with engine.connect() as conn:
        sql = "SELECT SUBSTR(timestamp, 1, 10) as dt, COUNT(*) as cnt FROM history WHERE timestamp >= :start"
        params = {"start": start_str}
        if user_id:
            sql += " AND user_id = :user_id"
            params["user_id"] = user_id
        sql += " GROUP BY dt ORDER BY cnt DESC LIMIT 1"
        
        daily_res = conn.execute(text(sql), params).fetchone()
        busiest_day = daily_res.dt if daily_res else "N/A"
        
    return {
        "total_searches": curr_searches,
        "total_pax": curr_pax,
        "avg_pax": curr_avg,
        "busiest_day": busiest_day,
        "trend_searches": change_searches,
        "trend_pax": change_pax,
        "trend_avg": change_avg
    }

def get_daily_stats(days=7, user_id=None):
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
        sql = '''
            SELECT SUBSTR(timestamp, 1, 10) as date_str, COUNT(*) as cnt 
            FROM history 
            WHERE timestamp >= :start_ts
        '''
        params = {"start_ts": start_date.strftime("%Y-%m-%d")}
        if user_id:
            sql += " AND user_id = :user_id"
            params["user_id"] = user_id
            
        sql += " GROUP BY date_str"
        
        result = conn.execute(text(sql), params)
        db_counts = {row.date_str: row.cnt for row in result}
        
        for d in date_list:
            stats.append({"date": d, "count": db_counts.get(d, 0)})
            
    return stats

def get_top_routes(days=7, limit=5, user_id=None):
    """
    Get most frequent routes from history in the last 'days' days.
    """
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d")

    with engine.connect() as conn:
        sql = '''
            SELECT route_info, COUNT(*) as cnt 
            FROM history 
            WHERE route_info IS NOT NULL AND route_info != '' AND timestamp >= :start
        '''
        params = {"limit": limit, "start": start_str}
        if user_id:
            sql += " AND user_id = :user_id"
            params["user_id"] = user_id
            
        sql += " GROUP BY route_info ORDER BY cnt DESC LIMIT :limit"
        
        result = conn.execute(text(sql), params)
        return [{"route": row.route_info, "count": row.cnt} for row in result]

def get_airline_stats(days=7, limit=1000, user_id=None):
    """
    Get airline distribution stats for the last 'days' days.
    """
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")

    with engine.connect() as conn:
        sql = "SELECT code FROM history WHERE timestamp >= :start"
        params = {"limit": limit, "start": start_str}
        if user_id:
            sql += " AND user_id = :user_id"
            params["user_id"] = user_id
        sql += " ORDER BY id DESC LIMIT :limit"
        
        result = conn.execute(text(sql), params)
        
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

def get_hourly_stats(days=7, limit=1000, user_id=None):
    """
    Get activity by hour of day (0-23) for the last 'days' days.
    """
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")

    with engine.connect() as conn:
        sql = "SELECT timestamp FROM history WHERE timestamp >= :start"
        params = {"limit": limit, "start": start_str}
        if user_id:
            sql += " AND user_id = :user_id"
            params["user_id"] = user_id
        sql += " ORDER BY id DESC LIMIT :limit"
        
        result = conn.execute(text(sql), params)
        
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

def get_all_history_for_export(user_id=None):
    """Returns all history for CSV export"""
    with engine.connect() as conn:
        sql = "SELECT * FROM history"
        params = {}
        if user_id:
            sql += " WHERE user_id = :user_id"
            params["user_id"] = user_id
        sql += " ORDER BY id DESC"
        
        result = conn.execute(text(sql), params)
        return [{
            "id": row.id,
            "timestamp": row.timestamp,
            "code": row.code,
            "passenger_info": row.passenger_info,
            "route_info": row.route_info
        } for row in result]

def get_customer_stats(days=30, limit=50):
    """
    Analyze customer loyalty (new vs returning) and find top customers.
    limit increased to 50 for scrollable list.
    """
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")

    with engine.connect() as conn:
        # Get all passenger info and code (only confirmed tickets)
        result = conn.execute(
            text("SELECT code, passenger_info FROM history WHERE timestamp >= :start AND code LIKE '%FA PAX%'"),
            {"start": start_str}
        )
        
        pax_counts = {}
        total_pax_entries = 0
        import re
        
        for row in result:
            p_info = row.passenger_info or ""
            code_text = row.code or ""
            if not p_info: continue
            
            # Extract valid passenger indices from code (e.g. /P1, /P2 in FA PAX lines)
            # Find all FA PAX lines
            # Use re.DOTALL to handle cases where /P is on the next line (indentation)
            fa_pax_matches = re.findall(r'FA PAX.*?/P(\d+)', code_text, re.DOTALL)
            valid_indices = set()
            if fa_pax_matches:
                valid_indices = {int(idx) for idx in fa_pax_matches}
            else:
                # Fallback: if FA PAX exists but regex fails, maybe count all? 
                # Or assume sequential? Let's assume sequential if we can't find specific P markers
                # but generally FA PAX has /P. If not found, we might skip or include all.
                # To be strict as requested: if no /P found but FA PAX exists, maybe it's a different format.
                # Let's count all if valid_indices is empty but FA PAX is present (which it is due to WHERE clause)
                # actually, to be safe, let's just use all if we can't match specific P-numbers
                pass

            # Split by lines (assuming each line is a passenger)
            # Format usually: "Passenger 1: NAME/SURNAME"
            lines = [l for l in p_info.split('\n') if l.strip()]
            
            for i, line in enumerate(lines):
                # 1-based index for current passenger line
                current_pax_idx = i + 1
                
                # Filter: Only include if this passenger index has a ticket
                if valid_indices and current_pax_idx not in valid_indices:
                    continue

                # Extract name logic
                name = line.strip().upper()
                
                # If it looks like "Passenger 1: NAME", split it
                if ':' in name:
                    parts = name.split(':', 1)
                    # Heuristic: if left side contains "Passenger" or digit, take right side
                    if "PASSENGER" in parts[0] or any(char.isdigit() for char in parts[0]):
                        name = parts[1].strip()
                
                # Basic cleanup
                for title in ["MR", "MS", "MRS", "MISS", "MSTR"]:
                    if name.endswith(" " + title):
                        name = name[:-(len(title)+1)].strip()
                    elif name.startswith(title + " "):
                        name = name[(len(title)+1):].strip()
                
                # Remove leading numbering like "1. "
                import re
                name = re.sub(r'^\d+\.?\s*', '', name)
                
                # Check for multiple names on one line (comma separated)
                # e.g. "ZHENG/YANGUANG, WANG/QI"
                if ',' in name:
                    sub_names = [n.strip() for n in name.split(',')]
                    for sub_name in sub_names:
                        if len(sub_name) < 2: continue
                        pax_counts[sub_name] = pax_counts.get(sub_name, 0) + 1
                        total_pax_entries += 1
                    continue # Skip adding the full line
                
                if len(name) < 2: continue # Skip very short names
                
                pax_counts[name] = pax_counts.get(name, 0) + 1
                total_pax_entries += 1
                
        # Calculate Stats
        unique_customers = len(pax_counts)
        returning_customers = sum(1 for count in pax_counts.values() if count > 1)
        new_customers = unique_customers - returning_customers
        
        repeat_rate = round((returning_customers / unique_customers * 100), 1) if unique_customers > 0 else 0
        
        # Top Customers
        sorted_pax = sorted(pax_counts.items(), key=lambda x: x[1], reverse=True)
        top_customers = [{"name": k, "count": v} for k, v in sorted_pax[:limit]]
        
        return {
            "total_pax_entries": total_pax_entries,
            "unique_customers": unique_customers,
            "returning_customers": returning_customers,
            "new_customers": new_customers,
            "repeat_rate": repeat_rate,
            "top_customers": top_customers
        }

def get_detailed_stats_aggregated(days=7, user_id=None):
    """
    Consolidated function to get all stats in a single DB connection.
    Drastically reduces latency for remote databases (like Neon on Render).
    """
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=days)
    start_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
    prev_start_date = start_date - datetime.timedelta(days=days)
    prev_start_str = prev_start_date.strftime("%Y-%m-%d %H:%M:%S")
    
    # Pre-calculate date list for daily stats
    date_list = []
    curr = start_date
    while curr <= now:
        date_list.append(curr.strftime("%Y-%m-%d"))
        curr += datetime.timedelta(days=1)
        
    stats = {}
    
    with engine.connect() as conn:
        # Base WHERE clause
        where_clause = "WHERE timestamp >= :start"
        params = {"start": start_date.strftime("%Y-%m-%d")}
        if user_id:
            where_clause += " AND user_id = :user_id"
            params["user_id"] = user_id

        # 1. Daily Stats
        sql_daily = text(f'''
            SELECT SUBSTR(timestamp, 1, 10) as date_str, COUNT(*) as cnt 
            FROM history 
            {where_clause}
            GROUP BY date_str
        ''')
        res_daily = conn.execute(sql_daily, params)
        daily_map = {row.date_str: row.cnt for row in res_daily}
        stats['daily'] = [{"date": d, "count": daily_map.get(d, 0)} for d in date_list]

        # 2. Top Routes
        sql_routes = text(f'''
            SELECT route_info, COUNT(*) as cnt 
            FROM history 
            {where_clause} AND route_info IS NOT NULL AND route_info != ''
            GROUP BY route_info 
            ORDER BY cnt DESC 
            LIMIT 5
        ''')
        res_routes = conn.execute(sql_routes, params)
        stats['top_routes'] = [{"route": row.route_info, "count": row.cnt} for row in res_routes]
        
        # 3. Airline Stats (Fetch raw codes to process in Python)
        # 4. Hourly Stats (Fetch timestamps to process in Python)
        # 5. Customer Stats (Fetch passenger_info/code)
        # We can fetch a larger dataset once and process in memory to avoid multiple queries
        
        # Need to reset params["start"] to full timestamp for this query
        params["start"] = start_str
        sql_raw = text(f"SELECT timestamp, code, passenger_info FROM history {where_clause}")
        res_raw = conn.execute(sql_raw, params)
        
        # Process in-memory
        import re
        airline_counts = {}
        hourly_counts = {h: 0 for h in range(24)}
        pax_counts = {}
        total_pax_entries = 0
        
        # KPI Accumulators
        kpi_total_searches = 0
        kpi_total_pax = 0
        kpi_ticketed_orders = 0
        
        raw_rows = [] 
        
        for row in res_raw:
            raw_rows.append(row)
            kpi_total_searches += 1
            ts = row.timestamp
            code = row.code or ""
            p_info = row.passenger_info or ""
            
            # Hourly
            try:
                if len(ts) >= 13:
                    h = int(ts[11:13])
                    hourly_counts[h] += 1
            except: pass
            
            # Airlines
            matches = re.findall(r'([A-Z0-9]{2})\d{3,4}', code)
            for al in matches:
                if not al.isdigit(): airline_counts[al] = airline_counts.get(al, 0) + 1
            
            # KPI Pax
            pax_tickets_in_code = code.count("FA PAX")
            if pax_tickets_in_code > 0:
                kpi_total_pax += pax_tickets_in_code
                kpi_ticketed_orders += 1
            
            # Customer Stats Logic (Simplified from get_customer_stats)
            if "FA PAX" in code and p_info:
                 # Extract names
                lines = [l for l in p_info.split('\n') if l.strip()]
                # Find valid indices if possible
                # Use re.DOTALL to match across lines (e.g. FA PAX ... \n ... /P1)
                fa_pax_matches = re.findall(r'FA PAX.*?/P(\d+)', code, re.DOTALL)
                valid_indices = {int(idx) for idx in fa_pax_matches} if fa_pax_matches else set()
                
                for i, line in enumerate(lines):
                    if valid_indices and (i + 1) not in valid_indices: continue
                    
                    name = line.strip().upper()
                    if ':' in name:
                        parts = name.split(':', 1)
                        if "PASSENGER" in parts[0] or any(c.isdigit() for c in parts[0]):
                            name = parts[1].strip()
                    
                    for title in ["MR", "MS", "MRS", "MISS", "MSTR"]:
                        if name.endswith(" " + title): name = name[:-(len(title)+1)].strip()
                        elif name.startswith(title + " "): name = name[(len(title)+1):].strip()
                    
                    name = re.sub(r'^\d+\.?\s*', '', name)
                    if ',' in name:
                         for sn in name.split(','):
                             sn = sn.strip()
                             if len(sn) < 2: continue
                             pax_counts[sn] = pax_counts.get(sn, 0) + 1
                             total_pax_entries += 1
                    else:
                        if len(name) < 2: continue
                        pax_counts[name] = pax_counts.get(name, 0) + 1
                        total_pax_entries += 1

        # Finish Airlines
        sorted_airlines = sorted([{"airline": k, "count": v} for k, v in airline_counts.items()], key=lambda x: x['count'], reverse=True)
        stats['airlines'] = sorted_airlines[:10]
        
        # Finish Hourly
        stats['hourly'] = [{"hour": f"{h:02d}:00", "count": hourly_counts[h]} for h in range(24)]
        
        # Finish Customers
        unique_customers = len(pax_counts)
        returning_customers = sum(1 for c in pax_counts.values() if c > 1)
        new_customers = unique_customers - returning_customers
        repeat_rate = round((returning_customers / unique_customers * 100), 1) if unique_customers > 0 else 0
        sorted_pax = sorted([{"name": k, "count": v} for k, v in pax_counts.items()], key=lambda x: x['count'], reverse=True)
        
        stats['customers'] = {
            "unique_customers": unique_customers,
            "returning_customers": returning_customers,
            "new_customers": new_customers,
            "repeat_rate": repeat_rate,
            "top_customers": sorted_pax[:50]
        }
        
        # Finish KPI (Current)
        curr_avg = round(kpi_total_pax / kpi_ticketed_orders, 1) if kpi_ticketed_orders > 0 else 0
        
        # KPI Previous Period (Need one more query)
        # To save latency, we do one count query for prev period
        
        # Build prev query
        prev_where = "WHERE timestamp >= :p_start AND timestamp < :p_end"
        prev_params = {"p_start": prev_start_str, "p_end": start_str}
        if user_id:
            prev_where += " AND user_id = :user_id"
            prev_params["user_id"] = user_id
            
        res_prev = conn.execute(text(f"SELECT code FROM history {prev_where}"), prev_params)
        
        prev_searches = 0
        prev_pax = 0
        prev_ticketed = 0
        
        for row in res_prev:
            prev_searches += 1
            c = row.code or ""
            pc = c.count("FA PAX")
            if pc > 0:
                prev_pax += pc
                prev_ticketed += 1
        
        prev_avg = round(prev_pax / prev_ticketed, 1) if prev_ticketed > 0 else 0
        
        def calc_change(c, p):
            if p == 0: return 100 if c > 0 else 0
            return round(((c - p) / p) * 100, 1)
            
        # Busiest Day
        busiest_day = "N/A"
        if daily_map:
            busiest_day = max(daily_map, key=daily_map.get)
            
        stats['kpi'] = {
            "total_searches": kpi_total_searches,
            "total_pax": kpi_total_pax,
            "avg_pax": curr_avg,
            "busiest_day": busiest_day,
            "trend_searches": calc_change(kpi_total_searches, prev_searches),
            "trend_pax": calc_change(kpi_total_pax, prev_pax),
            "trend_avg": calc_change(curr_avg, prev_avg)
        }
        
    return stats

# Initialize on import
init_db()
# Auto-cleanup on startup (keep 30 days of SEARCH history, preserve issued)
delete_old_history(30)

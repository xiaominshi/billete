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
        ("data_json", "TEXT")
    ]
    
    for col_name, col_type in columns_to_add:
        try:
            # Use engine.begin() to create a fresh transaction for EACH column
            # This ensures if one fails (e.g. column exists), others still run.
            # And avoids the "current transaction is aborted" error in Postgres.
            with engine.begin() as conn:
                try:
                    if dialect == "postgresql":
                        conn.execute(text(f"ALTER TABLE history ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                    else:
                        # SQLite doesn't support IF NOT EXISTS in ADD COLUMN consistently across versions
                        conn.execute(text(f"ALTER TABLE history ADD COLUMN {col_name} {col_type}"))
                except Exception as e:
                    # Ignore error only if it's likely "column exists"
                    # But print it for debugging
                    print(f"Migration note for {col_name}: {e}")
        except Exception as outer_e:
            print(f"Transaction error during migration for {col_name}: {outer_e}")

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

def add_history_entry(code, result, passenger_info, route_info, timestamp=None, cost=None, price=None, data_json=None):
    print(f"DEBUG: add_history_entry called. Code len: {len(code) if code else 0}")
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
        "data_json": data_json if data_json is not None else "{}"
    }

    try:
        # Use engine.begin() for atomic transaction management
        with engine.begin() as conn:
            # 1. Deduplication REMOVED to prevent locking and ensure history preservation
            # if code:
            #     conn.execute(text("DELETE FROM history WHERE code = :code"), {"code": code})
            
            # 2. Insert new record
            conn.execute(
                text('''
                    INSERT INTO history (timestamp, code, result, passenger_info, route_info, cost, price, data_json)
                    VALUES (:timestamp, :code, :result, :passenger_info, :route_info, :cost, :price, :data_json)
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
        daily_res = conn.execute(
            text("SELECT SUBSTR(timestamp, 1, 10) as dt, COUNT(*) as cnt FROM history WHERE timestamp >= :start GROUP BY dt ORDER BY cnt DESC LIMIT 1"),
            {"start": start_str}
        ).fetchone()
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
            fa_pax_matches = re.findall(r'FA PAX.*?/P(\d+)', code_text)
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

def get_detailed_stats_aggregated(days=7):
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
        # 1. Daily Stats
        sql_daily = text('''
            SELECT SUBSTR(timestamp, 1, 10) as date_str, COUNT(*) as cnt 
            FROM history 
            WHERE timestamp >= :start
            GROUP BY date_str
        ''')
        res_daily = conn.execute(sql_daily, {"start": start_date.strftime("%Y-%m-%d")})
        daily_map = {row.date_str: row.cnt for row in res_daily}
        stats['daily'] = [{"date": d, "count": daily_map.get(d, 0)} for d in date_list]

        # 2. Top Routes
        sql_routes = text('''
            SELECT route_info, COUNT(*) as cnt 
            FROM history 
            WHERE route_info IS NOT NULL AND route_info != '' AND timestamp >= :start
            GROUP BY route_info 
            ORDER BY cnt DESC 
            LIMIT 5
        ''')
        res_routes = conn.execute(sql_routes, {"start": start_date.strftime("%Y-%m-%d")})
        stats['top_routes'] = [{"route": row.route_info, "count": row.cnt} for row in res_routes]
        
        # 3. Airline Stats (Fetch raw codes to process in Python)
        # 4. Hourly Stats (Fetch timestamps to process in Python)
        # 5. Customer Stats (Fetch passenger_info/code)
        # We can fetch a larger dataset once and process in memory to avoid multiple queries
        # Fetching last 1000 entries or all within timeframe? 
        # Timeframe is safer.
        sql_raw = text("SELECT timestamp, code, passenger_info FROM history WHERE timestamp >= :start")
        res_raw = conn.execute(sql_raw, {"start": start_str})
        
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
                fa_pax_matches = re.findall(r'FA PAX.*?/P(\d+)', code)
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
        sql_prev = text("SELECT COUNT(*) as cnt, (SELECT COUNT(*) FROM history WHERE timestamp >= :p_start AND timestamp < :p_end AND code LIKE '%FA PAX%') as ticketed_rows FROM history WHERE timestamp >= :p_start AND timestamp < :p_end")
        # Note: Calculating precise pax/avg for previous period via single query is complex due to regex counting.
        # We will approximate or just run a second lightweight scan.
        # Actually, let's just run the separate simple counts. It's much faster than 6 full queries.
        
        # For Trend: we need Prev Total Searches, Prev Total Pax
        # Let's do a simple scan for prev period
        res_prev = conn.execute(text("SELECT code FROM history WHERE timestamp >= :p_start AND timestamp < :p_end"), 
                                {"p_start": prev_start_str, "p_end": start_str})
        
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
            
        # Busiest Day (Already computed in Daily loop? No, daily loop is strict range.
        # But we have daily_map from the daily query.
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

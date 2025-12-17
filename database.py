import sqlite3
import os
import json
import datetime

DB_NAME = "billete.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Airports table
    c.execute('''
        CREATE TABLE IF NOT EXISTS airports (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    
    # History table
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            code TEXT,
            result TEXT,
            passenger_info TEXT,
            route_info TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def get_all_airports():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM airports')
    rows = c.fetchall()
    conn.close()
    return {row['code']: row['name'] for row in rows}

def upsert_airport(code, name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO airports (code, name) VALUES (?, ?)
        ON CONFLICT(code) DO UPDATE SET name=excluded.name
    ''', (code.upper(), name))
    conn.commit()
    conn.close()

def delete_airport(code):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('DELETE FROM airports WHERE code = ?', (code.upper(),))
        row_count = c.rowcount
        conn.commit()
        conn.close()
        return row_count > 0
    except Exception as e:
        print(f"Delete Error: {e}")
        return False

def get_history_entries(limit=100):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM history ORDER BY id DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "timestamp": row['timestamp'],
            "code": row['code'],
            "result": row['result'],
            "passenger_info": row['passenger_info'],
            "route_info": row['route_info']
        })
    return history

def add_history_entry(code, result, passenger_info, route_info):
    conn = get_db_connection()
    c = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO history (timestamp, code, result, passenger_info, route_info)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, code, result, passenger_info, route_info))
    
    # Cleanup old > 7 days
    # Optional logic: DELETE FROM history WHERE timestamp < ... 
    # But for now, let's keep it simple or implement the logic from logic.py here.
    
    conn.commit()
    conn.close()

def clear_history_entries():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM history')
    conn.commit()
    conn.close()
    return True

# Initialize on import
init_db()

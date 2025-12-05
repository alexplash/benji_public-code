
import sqlite3

DB_PATH = "robot.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            speaker TEXT NOT NULL,
            message TEXT NOT NULL,
            msg_order INTEGER NOT NULL    
        )          
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )              
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            likes TEXT DEFAULT '[]',
            dislikes TEXT DEFAULT '[]'
        )              
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rl_profile (
            user_id INTEGER PRIMARY KEY,
            baseline_reward REAL NOT NULL DEFAULT 0.5,
            num_sessions INTEGER NOT NULL DEFAULT 0
        )              
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rl_traits (
            user_id INTEGER NOT NULL,
            trait_id INTEGER NOT NULL,
            trait_name TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 0.0,
            PRIMARY KEY (user_id, trait_id)
        )          
    """)
    
    conn.commit()
    conn.close()
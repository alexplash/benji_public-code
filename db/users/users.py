
from ..database import get_db
import json
import pandas as pd
import os

CURRENT_DIR = os.path.dirname(__file__)  # .../v2/db/users
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))  # .../v2
TRAITS_CSV_PATH = os.path.join(PROJECT_ROOT, "rl", "traits.csv") # v2/rl/traits.csv

TRAITS_DF = pd.read_csv(TRAITS_CSV_PATH)

def get_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row["id"], "name": row["name"]} for row in rows]

def create_user(name):
    conn = get_db()
    cursor = conn.cursor()
    
    # create row in users table
    cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
    user_id = cursor.lastrowid
    
    # create row in user_profile table
    cursor.execute("""
        INSERT INTO user_profile (user_id, likes, dislikes)
        VALUES (?, ?, ?)         
    """,
    (user_id, json.dumps([]), json.dumps([]))
    )
    
    # create row in rl_profile table
    cursor.execute("""
        INSERT INTO rl_profile (user_id, baseline_reward, num_sessions)
        VALUES (?, ?, ?)
    """,
    (user_id, 0.5, 0)
    )
    
    # create rows in rl_traits table
    rl_traits_rows = [
        (user_id, int(row['trait_id']), row['trait_name'], 0.0)
        for _, row in TRAITS_DF.iterrows()
    ]
    cursor.executemany("""
        INSERT INTO rl_traits (user_id, trait_id, trait_name, weight)
        VALUES (?, ?, ?, ?)                  
    """,
    rl_traits_rows
    )
    
    conn.commit()
    conn.close()
    return user_id

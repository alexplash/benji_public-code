
from ..database import get_db


def get_rl_profile(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, baseline_reward, num_sessions
        FROM rl_profile
        WHERE user_id = ?            
    """,
    (user_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    return {
        "user_id": row['user_id'],
        "baseline_reward": row['baseline_reward'],
        "num_sessions": row['num_sessions']
    }

def get_rl_traits(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT trait_id, trait_name, weight
        FROM rl_traits
        WHERE user_id = ?
        ORDER BY trait_id ASC              
    """,
    (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    traits = []
    for row in rows:
        traits.append({
            "trait_id": row['trait_id'],
            "trait_name": row['trait_name'],
            "weight": row['weight']
        })
    
    return traits

def save_trait_weights(user_id, traits):
    conn = get_db()
    cursor = conn.cursor()
    
    update_rows = [(trait['weight'], user_id, trait['trait_id']) for trait in traits]
    
    cursor.executemany("""
        UPDATE rl_traits
        SET weight = ?
        WHERE user_id = ?
        AND trait_id = ?             
    """,
    update_rows
    )
    
    conn.commit()
    conn.close()

def save_rl_profile(user_id, baseline_reward, num_sessions):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE rl_profile
        SET baseline_reward = ?, num_sessions = ?
        WHERE user_id = ?          
    """,
    (baseline_reward, num_sessions, user_id)
    )
    
    conn.commit()
    conn.close()
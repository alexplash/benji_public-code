
from ..database import get_db

def get_next_msg_order(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT MAX(msg_order) FROM conversation_history WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()[0]
    conn.close()
    return 1 if result is None else result + 1

def add_to_history(user_id, speaker, message):
    conn = get_db()
    cursor = conn.cursor()
    msg_order = get_next_msg_order(user_id)
    
    cursor.execute(
        """
        INSERT INTO conversation_history (user_id, speaker, message, msg_order)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, speaker, message, msg_order)
    )
    conn.commit()
    conn.close()

def get_history_as_string(user_id, limit = 20):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT speaker, message
        FROM conversation_history
        WHERE user_id = ?
        ORDER BY msg_order ASC
        LIMIT ?            
    """,
    (user_id, limit)
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    return "\n".join([f"{row['speaker']}: {row['message']}" for row in rows])
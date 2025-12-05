
from ..database import get_db
import json


def get_user_profile(user_id):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT likes, dislikes
        FROM user_profile
        WHERE user_id = ?       
    """,
    (user_id,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    try:
        likes = json.loads(row['likes']) if row['likes'] else []
    except:
        likes = []
    
    try:
        dislikes = json.loads(row['dislikes']) if row['dislikes'] else []
    except:
        dislikes = []
    
    return {
        "LIKES": likes,
        "DISLIKES": dislikes
    }
    
def update_user_profile(user_id, new_likes, new_dislikes, old_likes, old_dislikes):
    conn = get_db()
    cursor = conn.cursor()
    
    full_likes = old_likes.copy()
    full_likes.extend(new_likes)
    
    full_dislikes = old_dislikes.copy()
    full_dislikes.extend(new_dislikes)
    
    cursor.execute("""
        UPDATE user_profile
        SET likes = ?, dislikes = ?
        WHERE user_id = ?             
    """,
    (json.dumps(full_likes), json.dumps(full_dislikes), user_id)
    )
    
    conn.commit()
    conn.close()
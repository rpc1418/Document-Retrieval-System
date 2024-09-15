from flask import Flask, request, jsonify
import sqlite3
import time

app = Flask(__name__)

# Database file
DB_FILE = 'cache.db'

# Initialize SQLite database
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Create tables for caching and user tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_requests (
            user_id TEXT PRIMARY KEY,
            count INTEGER
        )
        ''')
        conn.commit()

# Initialize the database
init_db()

def get_cache(key):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM cache WHERE key=?', (key,))
        row = cursor.fetchone()
        return row[0] if row else None

def set_cache(key, value):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('REPLACE INTO cache (key, value) VALUES (?, ?)', (key, value))
        conn.commit()

def track_request(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT count FROM user_requests WHERE user_id=?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            count = row[0] + 1
            if count > 5:
                return False
            cursor.execute('UPDATE user_requests SET count=? WHERE user_id=?', (count, user_id))
        else:
            count = 1
            cursor.execute('INSERT INTO user_requests (user_id, count) VALUES (?, ?)', (user_id, count))
        
        conn.commit()
        return True

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "active"}), 200

@app.route('/search', methods=['GET'])
def search():
    user_id = request.args.get('user_id')
    text = request.args.get('text', '')
    top_k = int(request.args.get('top_k', 10))
    threshold = float(request.args.get('threshold', 0.5))

    if not track_request(user_id):
        return jsonify({"error": "Too many requests"}), 429

    # Check cache
    cache_key = f'search:{user_id}:{text}:{top_k}:{threshold}'
    cached_result = get_cache(cache_key)
    if cached_result:
        return jsonify({"results": eval(cached_result)}), 200

    # Perform the search operation (dummy implementation here)
    results = perform_search(text, top_k, threshold)
    set_cache(cache_key, str(results))
    
    return jsonify({"results": results}), 200

def perform_search(text, top_k, threshold):
    # Dummy search implementation; replace with actual search logic
    return [{"id": i, "result": f"Result {i} for {text}"} for i in range(top_k)]


if __name__ == '__main__':
    app.run(debug=True)

import logging  # Import the standard logging module
from flask import Flask, request, jsonify
import sqlite3
import time
import requests
from bs4 import BeautifulSoup
import threading

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Database file
DB_FILE = 'cache.db'

# Trusted news sources
TRUSTED_SOURCES = [
    "https://www.nytimes.com/",
    "https://www.bbc.com/news/",
    "https://www.washingtonpost.com/"
]

# Maximum number of documents to fetch per 5 minutes
MAX_DOCUMENTS_PER_FETCH = 100

# Initialize SQLite database
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Create tables for caching, user tracking, and documents
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
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT UNIQUE,
            text TEXT
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

    # Rate limit check
    if not track_request(user_id):
        return jsonify({"error": "Too many requests"}), 429

    # Check cache
    cache_key = f'search:{user_id}:{text}:{top_k}:{threshold}'
    cached_result = get_cache(cache_key)
    if cached_result:
        return jsonify({"results": eval(cached_result)}), 200

    # Perform the search operation
    results = perform_search(text, top_k, threshold)

    # Store the result in cache
    set_cache(cache_key, str(results))

    return jsonify({"results": results}), 200


def perform_search(text, top_k, threshold):
    # Retrieve documents from the database
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, url, text FROM documents')
        documents = cursor.fetchall()

    if not documents:
        return []

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer()
    document_texts = [doc[2] for doc in documents]  # Using the 'text' field from the documents
    document_vectors = vectorizer.fit_transform(document_texts)

    # Transform the query into a vector
    query_vector = vectorizer.transform([text])

    # Calculate cosine similarity between the query and all documents
    similarity_scores = cosine_similarity(query_vector, document_vectors)[0]

    # Filter documents based on similarity threshold
    results = [
        (documents[i], similarity_scores[i])
        for i in range(len(documents))
        if similarity_scores[i] >= threshold
    ]

    # Sort by similarity score in descending order
    results.sort(key=lambda x: x[1], reverse=True)

    # Limit the results to the top_k documents
    top_results = results[:top_k]

    # Format the results for output
    formatted_results = [
        {
            "id": doc[0],
            "url": doc[1],
            "text_snippet": doc[2][:200],  # Provide a snippet of the document text
            "similarity_score": score
        }
        for doc, score in top_results
    ]

    return formatted_results


# Check if the article title already exists in the database
def document_exists_by_title(title):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents WHERE title=?", (title,))
        return cursor.fetchone()[0] > 0

# Function to scrape articles from different sources
def scrape_articles():
    while True:
        documents_fetched = 0
        for source in TRUSTED_SOURCES:
            response = requests.get(source)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Adjust selectors based on the source's structure
            if source == "https://www.nytimes.com/":
                articles = soup.find_all('article', class_='css-1l8g93h')
            elif source == "https://www.bbc.com/news/":
                articles = soup.find_all('div', {'data-testid': 'card-text-wrapper'})
            elif source == "https://www.washingtonpost.com/":
                articles = soup.find_all('div', class_='article-card')  # Adjust selector as needed
            
            print(f"Found {len(articles)} articles on {source}")

            for article in articles:
                if documents_fetched >= MAX_DOCUMENTS_PER_FETCH:
                    break

                if source == "https://www.bbc.com/news/":
                    # Extract the title
                    title_tag = article.find('h2', {'data-testid': 'card-headline'})
                    title = title_tag.get_text(strip=True) if title_tag else 'No title found'

                    # Extract the description
                    description_tag = article.find('p', {'data-testid': 'card-description'})
                    description = description_tag.get_text(strip=True) if description_tag else 'No description found'

                    # Extract the URL
                    url_tag = article.find_parent('a', {'data-testid': 'internal-link'})
                    url = f"https://www.bbc.com{url_tag['href']}" if url_tag else 'No URL found'

                else:
                    # Example for other sources (NYTimes, WashingtonPost)
                    title_element = article.find('a', class_='gs-c-promo-heading')
                    if title_element:
                        title = title_element.text.strip()
                        url = title_element['href']
                    else:
                        continue

                    # Additional logic to extract content (if needed)
                    content_element = article.find('p', class_='some-content-class')
                    description = content_element.text.strip() if content_element else ""

                # Check if the document already exists by title
                if not document_exists_by_title(title):
                    # Store the article in the database
                    with sqlite3.connect(DB_FILE) as conn:
                        cursor = conn.cursor()
                        try:
                            cursor.execute('''
                                INSERT INTO documents (url, title, text)
                                VALUES (?, ?, ?)
                            ''', (url, title, description))
                            conn.commit()
                        except sqlite3.IntegrityError:
                            logging.getLogger(__name__).warning(f"Article with title '{title}' already exists.")
                    
                    documents_fetched += 1

        time.sleep(300)  # Wait 5 minutes before scraping again

# Start background scraping thread
thread = threading.Thread(target=scrape_articles)
thread.start()

if __name__ == '__main__':
    app.run(debug=True)

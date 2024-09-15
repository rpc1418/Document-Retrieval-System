import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DB_FILE = 'cache.db'

def fetch_documents():
    """Fetch all documents from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, url, text FROM documents')
        documents = cursor.fetchall()
    return documents

def perform_search(text, top_k=10, threshold=0.5):
    """Perform search using TF-IDF and cosine similarity."""
    # Fetch documents from the dataset
    documents = fetch_documents()

    if not documents:
        print("No documents found in the dataset.")
        return []

    # TF-IDF Vectorization
    vectorizer = TfidfVectorizer()
    document_texts = [doc[2] for doc in documents]  # Use the 'text' field from documents
    document_vectors = vectorizer.fit_transform(document_texts)

    # Transform the search query into a vector
    query_vector = vectorizer.transform([text])

    # Calculate cosine similarity between the query and the documents
    similarity_scores = cosine_similarity(query_vector, document_vectors)[0]

    # Filter documents based on the similarity threshold
    results = [
        (documents[i], similarity_scores[i])
        for i in range(len(documents))
        if similarity_scores[i] >= threshold
    ]

    # Sort the results by similarity score in descending order
    results.sort(key=lambda x: x[1], reverse=True)

    # Limit the results to the top_k
    top_results = results[:top_k]

    # Format and return the results
    formatted_results = [
        {
            "id": doc[0],
            "url": doc[1],
            "text_snippet": doc[2][:200],  # Return a snippet of the document text
            "similarity_score": score
        }
        for doc, score in top_results
    ]

    return formatted_results

# Test the perform_search function
if __name__ == "__main__":
    query_text = "irish"  # Replace with actual search query
    top_k_results = 5
    similarity_threshold = 0.2
    search_results = perform_search(query_text, top_k=top_k_results, threshold=similarity_threshold)
    
    if search_results:
        for result in search_results:
            print(f"ID: {result['id']}, URL: {result['url']}, Score: {result['similarity_score']}")
            print(f"Snippet: {result['text_snippet']}")
            print("="*50)
    else:
        print("No relevant documents found.")

# Document Retrieval System for Chat Applications

## Overview

This project is designed to build a **Document Retrieval System** for chat applications, enabling Large Language Models (LLMs) to generate contextual inferences. The backend retrieves documents, processes search queries, and caches responses for optimized performance.

## Key Features

- **Document Storage:** News articles are scraped periodically from trusted sources and stored in a database.
- **Search Endpoint:** Accepts a query, and returns the top-k most relevant documents using TF-IDF vectorization and cosine similarity.
- **Caching:** Responses are cached to improve performance for repeated queries.
- **User Request Tracking:** Tracks the number of requests per user, limiting API calls to 5 per user.
- **Rate Limiting:** Returns HTTP 429 error when a user exceeds 5 requests.
- **Background Scraping:** A separate thread scrapes news articles in the background every 5 minutes.
- **Health Check:** An endpoint is available to check if the service is running.
- **Dockerized:** The entire application is containerized using Docker for easy deployment.

## API Endpoints

### 1. `/health` [GET]
- **Purpose:** Check if the API is active.
- **Response:** `{ "status": "active" }`
  
### 2. `/search` [GET]
- **Purpose:** Retrieve relevant documents based on the query.
- **Parameters:**
  - `user_id` (required): The ID of the user making the request.
  - `text` (optional): The search query (default is an empty string).
  - `top_k` (optional): Number of top results to return (default is 10).
  - `threshold` (optional): Cosine similarity threshold (default is 0.5).
- **Response:** A list of top results, with each containing:
  - `id`: Document ID
  - `url`: URL of the document
  - `text_snippet`: A snippet of the document
  - `similarity_score`: Cosine similarity score

- **Rate Limiting:** After 5 requests, the user will receive HTTP 429.

## Caching Strategy

The caching system stores query results in a SQLite database (`cache.db`). SQLite is chosen for its ease of use in a local development setup and efficient read/write performance. For production environments, more scalable caching solutions like **Redis** or **SQLite with WAL mode** can be considered. 

### Why SQLite?

- **Compatibility with Windows:** SQLite is a lightweight and easy-to-setup database for quick caching, which integrates well with Python-based applications.
- **Disk-Based Storage:** Unlike in-memory caching systems (e.g., Memcached), SQLite allows persistent storage across server restarts.
- **Low Overhead:** Since the focus is on fast retrieval, SQLite provides sufficient speed for this use case with simple read and write queries.

## Database Structure

- **`cache` Table:** Stores cached search results.
  - `key`: A combination of the search parameters (`user_id`, `text`, `top_k`, `threshold`).
  - `value`: The cached search result.
  
- **`user_requests` Table:** Tracks the number of requests made by each user.
  - `user_id`: The ID of the user.
  - `count`: Number of API requests made by the user.
  
- **`documents` Table:** Stores scraped news articles.
  - `id`: Auto-incremented primary key.
  - `url`: URL of the news article.
  - `title`: Title of the news article.
  - `text`: Full text of the article.

## Background Scraper

The scraper runs in a separate thread and fetches articles from trusted news sources like:

- **New York Times**
- **BBC News**
- **Washington Post**

Articles are scraped every 5 minutes and inserted into the database, ensuring that the document retrieval system remains updated with the latest content.

## Running the Project

### Prerequisites

- **Python 3.8+**
- **Docker**

### Setup

  1. Clone the repository:
   ```bash
   git clone https://github.com/rpc1418/21BLC1098_ML
   cd 21BLC1098_ML
```
  2. Clone the repository:
   ```bash
   pip install -r requirements.txt

```
  3. Run the application:
   ```bash
python app.py
```
  4. To run in a Docker container:
   ```bash
docker build -t document-retrieval-system .
docker run -p 5000:5000 document-retrieval-system
```
### Docker
The project is Dockerized for easy deployment. Use the following command to build and run the Docker container:
```bash
docker build -t document-retrieval-system .
docker run -p 5000:5000 document-retrieval-system

```

## Performance and Logging

### Inference Time
For each search request, the time taken to compute results is logged.

### API Logging
Requests and responses are logged for debugging and tracking purposes.

## Limitations

- **Scaling**: While SQLite is sufficient for small-scale applications, more robust database systems like PostgreSQL are recommended for larger deployments.
- **Re-Ranking**: Re-ranking algorithms are not implemented but can be added for enhanced result accuracy.

## Future Improvements

- Implement fine-tuning scripts for retrievers.
- Incorporate re-ranking algorithms to improve the relevance of search results.
- Use Redis for caching in production environments for faster in-memory retrieval.

## Concurrency

The scraper runs in the background on a separate thread, ensuring non-blocking operations. The main Flask server handles user requests concurrently using Python’s threading module.

## Author

**Rudraksh Chourey**  
For any queries or issues, feel free to reach out.

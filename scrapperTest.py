import requests
from bs4 import BeautifulSoup

# Function to scrape articles from BBC News
def scrape_bbc_news():
    url = 'https://www.bbc.com/news'
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve content. Status code: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all articles based on data-testid attributes
    articles = soup.find_all('div', {'data-testid': 'card-text-wrapper'})
    print("here")
    print(articles)
    for article in articles:
        # Extract the title (h2 tag within data-testid="card-headline")
        title_tag = article.find('h2', {'data-testid': 'card-headline'})
        title = title_tag.get_text(strip=True) if title_tag else 'No title found'
        
        # Extract the description (p tag with data-testid="card-description")
        description_tag = article.find('p', {'data-testid': 'card-description'})
        description = description_tag.get_text(strip=True) if description_tag else 'No description found'
        
        # Extract the URL (find parent <a> tag with href)
        url_tag = article.find_parent('a', {'data-testid': 'internal-link'})
        article_url = f"https://www.bbc.com{url_tag['href']}" if url_tag else 'No URL found'

        # Print or return the extracted data
        print(f"Title: {title}")
        print(f"Description: {description}")
        print(f"URL: {article_url}\n")

# Run the scraper
scrape_bbc_news()

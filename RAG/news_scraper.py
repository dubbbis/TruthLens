import requests
import json
import time
from unstructured.partition.html import partition_html
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from newspaper import Article

# 🔹 CONFIGURATION: Set max articles to scrape
MAX_ARTICLES = 10  # Change this to 5, 10, 15, etc.

# API Key for NewsAPI
API_KEY = "d306519089ed41f798067a3c686b6226"
url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={API_KEY}"
response = requests.get(url)
articles = response.json().get("articles", [])[:MAX_ARTICLES]  # 🔹 Limit articles

# User-Agent Rotator
ua = UserAgent()

# List of known paywalled domains (avoid scraping these)
paywalled_domains = ["nytimes.com", "washingtonpost.com", "theatlantic.com", "bloomberg.com"]

def is_paywalled(url):
    """Check if the URL is from a known paywalled domain."""
    return any(domain in url for domain in paywalled_domains)

def extract_full_text(url):
    """Extracts full article text intelligently."""
    try:
        headers = {'User-Agent': ua.random}  # Use a rotating user-agent
        page = requests.get(url, headers=headers, timeout=10)

        # Check if the page is accessible
        if page.status_code != 200:
            return f"Error: Page returned status code {page.status_code}"

        # Step 1: Try `newspaper3k` (Best for Full-Text Extraction)
        article = Article(url)
        article.download()
        article.parse()
        if len(article.text) > 500:  # Ensure we got meaningful text
            return article.text

        # Step 2: Try `Unstructured` as a fallback
        elements = partition_html(text=page.text)
        extracted_text = "\n".join([el.text for el in elements if el.text.strip()])
        if len(extracted_text) > 500:
            return extracted_text

        # Step 3: Fallback to BeautifulSoup for last-resort extraction
        soup = BeautifulSoup(page.text, "html.parser")
        paragraphs = soup.find_all("p")
        extracted_text = "\n".join([p.get_text() for p in paragraphs])
        return extracted_text if len(extracted_text) > 500 else "Content could not be extracted."

    except Exception as e:
        return f"Error extracting content: {str(e)}"

# Process articles (LIMITED TO MAX_ARTICLES)
news_data = []
for i, a in enumerate(articles):
    url = a["url"]
    
    # Skip paywalled articles
    if is_paywalled(url):
        print(f"🚫 Skipping paywalled article: {url}")
        continue

    print(f"🔍 [{i+1}/{MAX_ARTICLES}] Scraping: {url}")
    full_text = extract_full_text(url)
    
    news_data.append({
        "title": a["title"],
        "url": url,
        "content": full_text
    })

    # Respect website rate limits (avoid bans)
    time.sleep(2)

# Save extracted articles to JSON
with open("news.json", "w", encoding="utf-8") as f:
    json.dump(news_data, f, indent=4)

print(f"✅ Scraped {len(news_data)} articles and saved to 'news.json'.")

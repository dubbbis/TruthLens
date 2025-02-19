import os
import json
import asyncio
import aiohttp
import re
import hashlib
import unicodedata
import sys
import argparse
from datetime import datetime, timedelta
from dateutil import parser
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory
from newspaper import Article  # Newspaper3k for full-text extraction
from unstructured.partition.html import partition_html  # Unstructured for full-text extraction
from urllib.parse import urlparse
from collections import defaultdict
import random
from dotenv import load_dotenv  # Import dotenv loader

# Load environment variables from .env
load_dotenv()

# CLI argument parsing for API Key
parser = argparse.ArgumentParser(description="News Scraper")
parser.add_argument("--api-key", type=str, help="API Key for Mediastack")
args = parser.parse_args()

def safe_user_agent():
    """Returns a safe user agent with rotation fallback."""
    try:
        ua = UserAgent()
        return ua.random
    except:
        return random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"
        ])

class NewsScraper:
    def __init__(self, api_key=None, max_articles=250, max_api_calls=5, max_concurrent_requests=10,
                 time_filter="last_week", start_date=None, end_date=None, randomize=False):
        self.api_key = api_key or args.api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("API key is required. Set it in .env or pass via --api-key.")

        self.max_articles = max_articles
        self.max_api_calls = max_api_calls
        self.api_calls_made = 0  # Track API calls
        self.news_dir = "NEWS_FILES"
        os.makedirs(self.news_dir, exist_ok=True)
        
        self.paywalled_domains = {"nytimes.com", "washingtonpost.com", "theatlantic.com", "bloomberg.com"}
        self.api_base_url = "http://api.mediastack.com/v1/news"
        
        DetectorFactory.seed = 0  # Ensures consistent language detection
        self.ua = safe_user_agent()
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
        self.time_filter = time_filter
        self.start_date = start_date
        self.end_date = end_date
        self.randomize = randomize
        self.seen_sources = set()
        self.article_hashes = set()
        self.source_counts = defaultdict(int)  # ✅ Track articles per source

    def get_time_filter(self):
        """Returns a tuple of (start_date, end_date) for filtering articles."""
        today = datetime.utcnow()
        if self.time_filter == "today":
            return today - timedelta(days=1), today
        elif self.time_filter == "last_week":
            return today - timedelta(days=7), today
        elif self.time_filter == "last_month":
            return today - timedelta(days=30), today
        elif self.time_filter == "custom" and self.start_date and self.end_date:
            return self.start_date, self.end_date
        return today - timedelta(days=7), today

    def clean_text(self, text):
        """Cleans up extracted text for better readability."""
        if not text:
            return ""
        # Remove unwanted whitespace, symbols, and URLs
        text = re.sub(r"\s+", " ", text)  # Collapse multiple spaces into one
        text = re.sub(r"http\S+", "", text)  # Remove URLs
        text = re.sub(r"[^\x00-\x7F]+", "", text)  # Remove non-ASCII characters (optional)
        text = unicodedata.normalize("NFKC", text)  # Normalize unicode characters
        return text.strip()

    def get_article_hash(self, title, content):
        """Generates a hash to prevent duplicate articles."""
        return hashlib.sha256(f"{title}{content}".encode()).hexdigest()

    async def fetch_with_retries(self, session, url, params=None, max_retries=3):
        """Fetches data with retries on failure."""
        for attempt in range(max_retries):
            try:
                headers = {"Authorization": f"Bearer {self.api_key}", "User-Agent": self.ua}
                async with session.get(url, headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 422:
                        print("🚨 Received status 422: Stopping execution.")
                        sys.exit(1)
                    print(f"⚠️ Attempt {attempt + 1}: Received status {response.status}")
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1}: Error fetching {url}: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return None

    async def extract_full_text(self, session, url):
        """Extracts article content using newspaper3k, Unstructured, and BeautifulSoup asynchronously."""
        try:
            headers = {'User-Agent': self.ua}
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    return f"Error: Page returned status code {response.status}"
                html = await response.text()
                
                # Try newspaper3k
                article = Article(url)
                article.download()
                article.html = html  # Manually assign HTML content
                article.parse()
                if len(article.text) > 500:
                    return article.text
                
                # Try Unstructured
                elements = partition_html(text=html)
                extracted_text = "\n".join([el.text for el in elements if el.text.strip()])
                if len(extracted_text) > 500:
                    return extracted_text
                
                # Try BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                paragraphs = soup.find_all("p")
                extracted_text = "\n".join([p.get_text() for p in paragraphs])
                return extracted_text if len(extracted_text) > 500 else "Content could not be extracted."
        except Exception as e:
            return f"Error extracting content: {str(e)}"

    async def fetch_articles(self):
        """Fetches articles from the API in batches with quality checks and includes full text processing."""
        all_articles = []
        domain_limit = 3  # Limit number of articles per domain (e.g., 3 articles per domain)
        no_new_articles_count = 0  # Track how many consecutive calls have resulted in no new articles
        
        start_date, end_date = self.get_time_filter()
        params = {
            "access_key": self.api_key,
            "languages": "en",
            "limit": 100,  # Maximum allowed per call
            "date": f"{start_date.strftime('%Y-%m-%d')},{end_date.strftime('%Y-%m-%d')}"
        }
        
        async with aiohttp.ClientSession() as session:
            while self.api_calls_made < self.max_api_calls and len(all_articles) < self.max_articles and no_new_articles_count < 3:
                self.api_calls_made += 1  # ✅ Track API calls correctly
                print(f"⏳ Attempt {self.api_calls_made}: Fetching articles...")

                response = await self.fetch_with_retries(session, self.api_base_url, params)
                
                if response:
                    # Track the number of articles collected from each domain
                    domain_count = defaultdict(int)
                    new_articles = []  # Temporarily hold newly fetched articles for this attempt
                    
                    tasks = []  # List of tasks for full text extraction
                    
                    for article in response.get("data", []):
                        if len(all_articles) >= self.max_articles:
                            break
                    
                        # Article basic fields
                        domain = urlparse(article["url"]).netloc
                        title = article.get("title", "").strip()
                        description = article.get("description", "").strip()
                        url = article.get("url", "")  # Use the article URL for scraping full content
                        published_date = article.get("published_at", "")
                        author = article.get("author", "Unknown author")
                        
                        # Quality Checks:
                        # 1. Article should have a title and a description
                        if not title or not description:
                            continue
                        
                        # 2. Check article length: Minimum content length (e.g., 50 words or 200 characters)
                        if len(description.split()) < 50:
                            continue
                        
                        # 3. Check for spammy domains (known bad domains)
                        if domain in self.paywalled_domains:
                            continue
                        
                        # 4. Language filter: Make sure the article is in English
                        if article.get("language", "en") != "en":
                            continue
                        
                        # 5. Avoid duplicates based on hash or URL
                        article_hash = self.get_article_hash(title, description)
                        if article_hash in self.article_hashes:
                            continue
                        
                        # Limit articles per domain
                        if domain_count[domain] >= domain_limit:
                            continue
                        domain_count[domain] += 1

                        # Add the full-text extraction task
                        tasks.append(self.extract_full_text(session, url))
                    
                    # Wait for all content extraction tasks to complete
                    full_texts = await asyncio.gather(*tasks)
                    
                    # Update the articles with the full content
                    for i, text in enumerate(full_texts):
                        if len(all_articles) < self.max_articles:  # Only update if still collecting
                            article_data = {
                                "author": self.clean_text(author),
                                "title": self.clean_text(title),
                                "description": self.clean_text(description),
                                "url": url,
                                "source": article.get("source", "Unknown source"),
                                "category": article.get("category", "Unknown category"),
                                "language": article.get("language", "Unknown language"),
                                "country": article.get("country", "Unknown country"),
                                "published_date": published_date,
                                "content": self.clean_text(text)  # Save the full content in the JSON
                            }
                            new_articles.append(article_data)
                            self.article_hashes.add(article_hash)  # Track this article as processed

                    # If new articles were fetched, add them to the total list
                    if new_articles:
                        all_articles.extend(new_articles)
                        no_new_articles_count = 0  # Reset count of no new articles
                        print(f"✅ Retrieved {len(new_articles)} new articles in this attempt.")
                    else:
                        no_new_articles_count += 1  # Increment the no new articles counter
                        print(f"⚠️ No new articles retrieved in this attempt.")

                    print(f"✅ Retrieved {len(all_articles)} articles so far.")
                else:
                    print("❌ Skipping this batch due to an API error.")

                # Wait before making another API call
                if self.api_calls_made < self.max_api_calls and no_new_articles_count < 3:
                    print("⏳ Waiting 30 seconds before making another API call...")
                    await asyncio.sleep(30)
            
            # If no new articles were retrieved after several attempts, stop fetching
            if no_new_articles_count >= 3:
                print("❌ No new articles were retrieved in the last 3 attempts. Stopping fetch and saving.")
            
        return all_articles


# This is the updated save_articles function, which now works asynchronously
async def save_articles(scraper):
    articles = await scraper.fetch_articles()  # Fetch articles asynchronously
    if articles:
        # ✅ Ensure NEWS_FILES directory exists
        os.makedirs(scraper.news_dir, exist_ok=True)

        # ✅ Generate a unique timestamped filename (YYYY-MM-DD_HH-MM-SS)
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"news_{date_str}.json"
        filepath = os.path.join(scraper.news_dir, filename)  # Save inside NEWS_FILES directory

        # ✅ Save JSON file inside NEWS_FILES
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=4)

        print(f"✅ {len(articles)} articles saved in '{filepath}'.")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    scraper = NewsScraper()  # Create the scraper object
    asyncio.run(save_articles(scraper))  # Fetch and save articles asynchronously

# To run the scraper
#
# In gitbash: 
# 
# pip install aiohttp beautifulsoup4 fake_useragent langdetect python-dateutil python-dotenv newspaper3k unstructured
#
# python data_collect.py

# Or with your own API Key
# python data_collect.py --api-key YOUR_API_KEY

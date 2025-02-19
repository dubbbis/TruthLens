import os
import json
import asyncio
import aiohttp
import re
from datetime import datetime, timedelta
from fake_useragent import UserAgent
from newspaper import Article
from bs4 import BeautifulSoup
from unstructured.partition.html import partition_html
from langdetect import detect, DetectorFactory
from urllib.parse import urlparse, urlunparse
import random
from collections import defaultdict
import time


## Set article amount limit
MAX_ARTICLES = 30
API_KEY = "356bb7cd80f02083d604ba6ba1dfadd8"

# ✅ Setup directories & constants
NEWS_DIR = "NEWS_FILES"
os.makedirs(NEWS_DIR, exist_ok=True)

BASE_URL = f"http://api.mediastack.com/v1/news?access_key={API_KEY}&countries=us&limit={MAX_ARTICLES}"
ua = UserAgent()

# Paywalled domains (skip articles from these sources)
paywalled_domains = {"nytimes.com", "washingtonpost.com", "theatlantic.com", "bloomberg.com"}

# Ensures consistent language detection results
DetectorFactory.seed = 0  

def is_paywalled(url):
    """Check if an article belongs to a paywalled domain."""
    return any(domain in url for domain in paywalled_domains)

def clean_text(text):
    """Cleans extracted text: removes excessive whitespace, special characters, and normalizes content."""
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)  # Remove extra whitespace/newlines
    text = re.sub(r"http\S+", "", text)  # Remove links
    text = re.sub(r"[^\x00-\x7F]+", " ", text)  # Remove non-ASCII characters
    return text.strip()

def detect_language(text):
    """Detects language of extracted text and filters non-English articles."""
    try:
        lang = detect(text)
        return lang == "en"  # Only accept English articles
    except:
        return False

def normalize_url(url):
    """Removes tracking parameters from URLs."""
    parsed_url = urlparse(url)
    clean_url = urlunparse(parsed_url._replace(query=""))  # Remove query params
    return clean_url

# ✅ Asynchronous content extraction
async def extract_full_text(session, url):
    """Extracts article content using multiple methods asynchronously."""
    try:
        headers = {'User-Agent': ua.random}
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status != 200:
                return None  # Skip failed articles

            html = await response.text()

            # ✅ Try newspaper3k
            article = Article(url)
            article.download()
            article.html = html  
            article.parse()
            if len(article.text) > 500:
                cleaned_text = clean_text(article.text)
                return cleaned_text if detect_language(cleaned_text) else None

            # ✅ Try Unstructured
            elements = partition_html(text=html)
            extracted_text = "\n".join([el.text for el in elements if el.text.strip()])
            if len(extracted_text) > 500:
                cleaned_text = clean_text(extracted_text)
                return cleaned_text if detect_language(cleaned_text) else None

            # ✅ Try BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            paragraphs = soup.find_all("p")
            extracted_text = "\n".join([p.get_text() for p in paragraphs])
            cleaned_text = clean_text(extracted_text)

            return cleaned_text if len(cleaned_text) > 500 and detect_language(cleaned_text) else None

    except Exception as e:
        return None  # Skip if extraction fails


async def fetch_articles(base_url):
    """Fetches news articles and extracts content asynchronously with domain limits and retry logic."""
    async with aiohttp.ClientSession() as session:
        try:
            articles_list = []
            seen_urls = set()  # Prevent duplicate articles
            domain_count = defaultdict(int)  # Track number of articles per domain
            max_articles_per_domain = 5  # Adjust as needed
            one_week_ago = datetime.utcnow() - timedelta(days=7)
            min_valid_articles = 30  # The goal number of good articles
            MAX_FETCH_ATTEMPTS = 100  # Soft limit on how many total attempts we make
            attempt_count = 0  # Track how many times we try
            start_time = time.time()  # Track total execution time
            MAX_RUNTIME_SECONDS = 60  # Stop fetching after 60 seconds if stuck

            while len(articles_list) < min_valid_articles and attempt_count < MAX_FETCH_ATTEMPTS:
                attempt_count += 1
                async with session.get(base_url) as response:
                    if response.status != 200:
                        print(f"🚨 Failed to fetch news: {response.status}")
                        return []

                    news_data = await response.json()
                    articles = news_data.get("data", [])

                for i, article in enumerate(articles):
                    if len(articles_list) >= min_valid_articles:
                        break  # Stop if we have enough valid articles

                    url = article.get("url", "")
                    if not url or is_paywalled(url):
                        continue

                    clean_url = normalize_url(url)
                    if clean_url in seen_urls:
                        continue  # Skip duplicate articles

                    # ✅ Extract domain name from URL
                    domain = urlparse(clean_url).netloc.replace("www.", "")
                    if domain_count[domain] >= max_articles_per_domain:
                        continue  # Limit number of articles per domain

                    # ✅ Check if article is recent (within last 7 days)
                    published_date = article.get("published_at", "Unknown date")
                    try:
                        article_date = datetime.strptime(published_date, "%Y-%m-%dT%H:%M:%S%z").date()
                        if article_date < one_week_ago.date():
                            continue
                    except Exception:
                        pass  # Keep article if date format is invalid

                    seen_urls.add(clean_url)
                    domain_count[domain] += 1  # Increase domain count

                    print(f"🔍 [{len(articles_list) + 1}] Processing: {clean_url}")
                    extracted_text = await extract_full_text(session, clean_url)

                    if extracted_text:  # Only keep articles with valid extracted text
                        articles_list.append({
                            "title": article.get("title", "Unknown title"),
                            "url": clean_url,
                            "published_date": published_date,
                            "source_name": article.get("source", "Unknown source"),
                            "author": article.get("author") if article.get("author") else "Unknown author",
                            "category": article.get("category", "Unknown category"),
                            "content": extracted_text,
                        })

                # ✅ Check if we should stop
                if len(articles_list) >= min_valid_articles:
                    break  # Stop if we have enough articles

                # ✅ Stop if the loop runs for too long
                if time.time() - start_time > MAX_RUNTIME_SECONDS:
                    print("⏳ Time limit reached, stopping article collection.")
                    break

            # ✅ Log final results
            print(f"✅ Collected {len(articles_list)} valid articles after {attempt_count} attempts.")

            return articles_list

        except Exception as e:
            print(f"❌ Error fetching articles: {str(e)}")
            return []



async def save_articles():
    """Fetches, cleans, and saves articles to JSON."""
    articles = await fetch_articles(BASE_URL)
    if articles:
        os.makedirs(NEWS_DIR, exist_ok=True)

        # ✅ Generate a unique timestamped filename (YYYY-MM-DD_HH-MM-SS)
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"news_{date_str}.json"
        filepath = os.path.join(NEWS_DIR, filename)

        # ✅ Save JSON file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=4)

        print(f"✅ {len(articles)} articles saved in '{filepath}'.")

if __name__ == "__main__":
    try:
        asyncio.get_running_loop().run_until_complete(save_articles())
    except RuntimeError:
        asyncio.run(save_articles())


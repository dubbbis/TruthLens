import os
import json
import asyncio
import aiohttp
import hashlib
import unicodedata
import random
import re
import traceback
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
import chromadb
from fake_useragent import UserAgent
from newspaper import Article
from bs4 import BeautifulSoup
from unstructured.partition.html import partition_html
from playwright.async_api import async_playwright
import brotli  # ✅ Import Brotli for manual decompression if needed


# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Directory for optional JSON storage
NEWS_DIR = "NEWS_FILES"
os.makedirs(NEWS_DIR, exist_ok=True)

BASE_URL = "http://api.mediastack.com/v1/news"


class NewsDatabase:
    def __init__(self, db_client):
        self.news_collection = db_client.get_or_create_collection(
            name="news_articles",
            metadata={"hnsw:space": "cosine"}  # Ensure proper vector search settings
        )
        self.articles_batch = []
        self.total_articles_saved = 0

        # ✅ Load existing article IDs ONCE at startup
        existing_data = self.news_collection.get(include=["metadatas"])  # Fetch metadata instead of "ids"

        # Extract existing IDs from metadata if they exist
        if existing_data and "metadatas" in existing_data:
            self.existing_ids = set(article["hash"] for article in existing_data["metadatas"] if "hash" in article)
        else:
            self.existing_ids = set()




    def buffer_article(self, article_data):
        """Stores articles in memory first, then writes all at once per API call."""
        if "hash" not in article_data or not article_data["hash"]:
            print(f"⚠️ Skipping article with missing hash: {article_data}")
            return  # Ignore articles without a valid hash

        if article_data["hash"] in self.existing_ids:
            print(f"🚫 Skipping duplicate (already in DB): {article_data['hash']}")
            return  # Skip duplicate

        cleaned_metadata = {k: (v if v is not None else "") for k, v in article_data.items()}
        self.articles_batch.append(cleaned_metadata)
        print(f"✅ Buffered new article: {article_data['hash']}")



    def commit_articles(self):
        """Writes all stored articles to ChromaDB at once, then clears memory."""
        if not self.articles_batch:
            print("⚠️ No articles to save.")
            return  # No articles to save

        try:
            print(f"🛠️ Preparing to send {len(self.articles_batch)} articles to ChromaDB...")

            # Ensure only unique IDs
            unique_articles = {article["hash"]: article for article in self.articles_batch}.values()
            valid_ids = [article["hash"] for article in unique_articles]

            if not valid_ids:
                print("⚠️ No valid unique IDs found, skipping ChromaDB commit.")
                return  # Prevent sending an empty list

            print(f"🔄 Final Articles to Save: {len(valid_ids)}")
            print(f"📜 Sample Article: {valid_ids[0]}")

            self.news_collection.add(
                ids=valid_ids,
                metadatas=list(unique_articles)
            )
            print(f"🗂️ ChromaDB updated: {len(unique_articles)} new unique articles added.")

            # Update existing_ids set
            self.existing_ids.update(valid_ids)

            # Clear batch for the next call
            self.articles_batch = []

        except Exception as e:
            print(f"⚠️ Error saving batch to ChromaDB: {e}")






class NewsScraper:
    def __init__(self, api_key=None, max_articles=250, max_api_calls=5, time_filter="last_month", save_json=True):
        self.api_key = api_key or API_KEY
        self.database = NewsDatabase(db_client)
        self.max_articles = max_articles
        self.max_api_calls = max_api_calls
        self.time_filter = time_filter
        self.save_json = save_json
        self.browser = None  # 🔴 Store a persistent browser instance
        self.articles_fetched = 0
        self.source_count = defaultdict(int)
        self.duplicate_hashes = set()
        self.wait_time = 15  # Default wait time

        # ✅ Move the API key check to the start
        if not self.api_key:
            raise ValueError("API_KEY is missing. Please set it in the .env file.")

        # ✅ Initialize headers AFTER self is fully initialized
        self.headers = {
            "User-Agent": self.safe_user_agent(),  # ✅ Now self is properly set up
            "Referer": "https://www.google.com/",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "DNT": "1",  # Do Not Track
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    async def start_browser(self):
        """Starts Playwright only if it's not running."""
        if not hasattr(self, "playwright") or self.playwright is None:
            self.playwright = await async_playwright().start()
        if self.browser is None:
            self.browser = await self.playwright.chromium.launch(headless=True)
        print("🌐 Playwright browser started.")


    async def close_browser(self):
        """Safely closes Playwright browser instance without crashing."""
        if self.browser:
            try:
                await self.browser.close()
                print("🛑 Playwright browser closed.")
            except Exception as e:
                print(f"⚠️ Error closing Playwright: {e}")
            finally:
                self.browser = None  # Ensure the reference is removed

        if hasattr(self, "playwright") and self.playwright:
            try:
                await self.playwright.stop()
                print("🔄 Playwright stopped successfully.")
            except RuntimeError as e:
                if "Event loop is closed" in str(e):
                    print("⚠️ Cannot stop Playwright: Event loop is already closed.")
                else:
                    print(f"⚠️ Error stopping Playwright: {e}")
            finally:
                self.playwright = None  # Ensure cleanup






    def scrape_article(self, article_data):
        """Scrapes an article and saves it to buffer."""
        self.database.buffer_article(article_data)
    
    def finalize_scraping(self):
        """Saves all buffered articles to the database before clearing memory."""
        self.save_all_articles_to_json()  # ✅ Save articles before committing to DB
        self.database.commit_articles()

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


    @staticmethod
    def safe_user_agent():
        """Returns a safe user agent with fallback rotation."""
        try:
            return UserAgent().random
        except:
            fallback_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"
            ]
            return random.choice(fallback_agents)


    @staticmethod
    def get_article_hash(title, description):
        """Generates a hash to check for duplicates before full text extraction."""
        return hashlib.sha256(f"{title}{description}".encode()).hexdigest()

    @staticmethod
    def clean_text(text):
        """Cleans up extracted text for better readability."""
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"http\S+", "", text)
        text = unicodedata.normalize("NFKC", text)
        return text.strip()

    def save_all_articles_to_json(self):
        """Saves all collected articles to a single JSON file at the end of an API call."""
        if not self.database.articles_batch:  # ✅ Corrected reference to articles_batch
            return  # No articles to save

        timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H-%M")
        json_path = os.path.join(NEWS_DIR, f"news_{timestamp}.json")

        # Load existing data if file exists
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
        else:
            existing_data = []

        # ✅ Append new articles correctly
        existing_data.extend(self.database.articles_batch)

        # Save back to JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)

        print(f"📄 JSON saved: {json_path}")

        # ✅ Clear batch after saving
        self.database.articles_batch = []

    

    async def fetch_js_page(self, url):
        """Fetches page content using a persistent Playwright browser session."""
        if self.browser is None:
            await self.start_browser()  # Ensure the browser is started before use

        page = await self.browser.new_page()
        try:
            await page.goto(url, timeout=10000)
            content = await page.content()
            return content
        except Exception as e:
            print(f"⚠️ Playwright error fetching {url}: {e}")
            return ""  # Always return a string even on failure
        finally:
            await page.close()  # ✅ Always close the page but keep the browser open


    async def extract_full_text(self, session, url):
        """Extracts full text with multiple fallback methods, including JavaScript rendering."""
        extracted_text = ""  # Ensure we always return a string

        # 1️⃣ Fetch raw HTML (normal request)
        try:
            async with session.get(url, headers=self.headers, timeout=10, compress=True) as response:
                if response.status != 200:
                    print(f"⚠️ Failed to fetch {url} (Status Code: {response.status})")
                    return ""  # Return empty string on failure
                html = await response.text()
        except aiohttp.ClientError as e:
            print(f"⚠️ Network error fetching {url}: {e}")
            return ""
        except asyncio.TimeoutError:
            print(f"⏳ Timeout fetching {url}")
            return ""

        # 2️⃣ Try BeautifulSoup (Fastest)
        try:
            soup = BeautifulSoup(html, "html.parser")
            paragraphs = soup.find_all("p")
            extracted_text = "\n".join([p.get_text() for p in paragraphs])
            if extracted_text and len(extracted_text) > 500:
                return self.clean_text(extracted_text)
        except Exception as e:
            print(f"⚠️ BeautifulSoup failed for {url}: {e}")

        # 3️⃣ Try Unstructured if BeautifulSoup fails
        try:
            text_elements = partition_html(text=html)
            extracted_text = " ".join([elem.text for elem in text_elements if elem.text.strip()])
            if extracted_text and len(extracted_text) > 500:
                return self.clean_text(extracted_text)
        except Exception as e:
            print(f"⚠️ Unstructured parsing failed for {url}: {e}")

        # 4️⃣ If both BeautifulSoup & Unstructured fail, try Playwright (JavaScript rendering)
        try:
            print(f"🔄 Fetching {url} with Playwright...")
            js_html = await self.fetch_js_page(url)  # ✅ Fetch dynamically rendered HTML
            soup = BeautifulSoup(js_html, "html.parser")
            paragraphs = soup.find_all("p")
            extracted_text = "\n".join([p.get_text() for p in paragraphs])
            if extracted_text and len(extracted_text) > 500:
                return self.clean_text(extracted_text)
        except Exception as e:
            print(f"⚠️ Playwright failed for {url}: {e}")

        # 5️⃣ If all else fails, use Newspaper3k
        try:
            article = Article(url, browser_user_agent=self.safe_user_agent())
            article.download()
            article.parse()
            extracted_text = article.text
            if extracted_text and len(extracted_text) > 500:
                return self.clean_text(extracted_text)
        except Exception as e:
            print(f"⚠️ Newspaper3k failed for {url}: {e}")

        return self.clean_text(extracted_text)  # ✅ Always return a string

    async def fetch_articles(self):
        """Fetches articles with improved API query handling and optimized checks."""
        async with aiohttp.ClientSession() as session:
            for call in range(self.max_api_calls):
                if self.articles_fetched >= self.max_articles:
                    break  # Stop if max articles are fetched
                
                failed_requests = []  # ✅ Track failed URLs and their status codes

                print(f"📡 API Call {call + 1}/{self.max_api_calls} | Offset: {call * 100}")

                # Set the offset dynamically for pagination
                params = {
                    "access_key": self.api_key,
                    "countries": "us",
                    "limit": 100,  # Max articles per request
                    "offset": call * 100  # Offset ensures we fetch different articles each call
                }

                # ✅ Use `self.headers` instead of redefining headers
                async with session.get(BASE_URL, params=params, headers=self.headers, timeout=10, compress=True) as response:
                    if response.status != 200:
                        print(f"🚨 API Request Failed (Status Code: {response.status})")
                        continue  # Skip to the next API call if request fails

                    try:
                        # ✅ Read raw response data
                        raw_data = await response.read()

                        # ✅ Manually decompress Brotli if needed
                        if response.headers.get("Content-Encoding") == "br":
                            raw_data = brotli.decompress(raw_data)  # 🔥 Decompress Brotli response

                        # ✅ Convert to JSON
                        news_data = json.loads(raw_data.decode("utf-8"))
                        articles = news_data.get("data", [])

                        if not isinstance(articles, list):  # Ensure "data" is a list
                            raise ValueError("Invalid API response format.")

                    except Exception:
                        print(f"⚠️ Error parsing API response: {traceback.format_exc()}")
                        continue

                    for article in articles:
                        if self.articles_fetched >= self.max_articles:
                            break

                        url = article.get("url", "")
                        title = article.get("title", "Unknown title")
                        description = article.get("description", "No description available")
                        source = article.get("source", "Unknown source")

                        article_hash = self.get_article_hash(title, description)

                        # Check for duplicates
                        if article_hash in self.duplicate_hashes or self.source_count[source] >= 5:
                            continue

                        # Extract full content
                        full_content = await self.extract_full_text(session, url)
                        if not full_content or len(full_content) < 500:
                            failed_requests.append((url, "Content Too Short"))  # ✅ Track short content failures
                            continue

                        # Store article
                        article["hash"] = article_hash
                        article["content"] = full_content
                        self.database.buffer_article(article)
                        self.source_count[source] += 1
                        self.articles_fetched += 1

                # ✅ Print final API call summary
                print(f"✅ Finished API Call {call + 1}/{self.max_api_calls} | Articles fetched: {self.articles_fetched}/{self.max_articles}")

                # ✅ Print failure summary (if any)
                if failed_requests:
                    failure_counts = {}
                    for _, reason in failed_requests:
                        failure_counts[reason] = failure_counts.get(reason, 0) + 1
                    print(f"⚠️ Failed Requests Summary: {failure_counts}")

                # Wait between API calls if needed
                if call < self.max_api_calls - 1 and self.articles_fetched < self.max_articles:
                    print(f"⏳ Waiting {self.wait_time} seconds before next API call...")
                    await asyncio.sleep(self.wait_time)
            # Save all articles fetched in this batch
        print(f"🔄 Final check: {len(self.database.articles_batch)} articles in batch before commit.")
        print(f"📝 Total unique articles fetched this run: {self.articles_fetched}")
        if not self.database.articles_batch:
            print("⚠️ No articles to commit to ChromaDB.")
        else:
            self.database.commit_articles()
        print(f"✅ Committed {len(self.database.articles_batch)} articles to ChromaDB.")

if __name__ == "__main__":
    # ✅ Initialize ChromaDB client
    db_client = chromadb.PersistentClient(path="./chroma_db")

    # ✅ Ensure "news_articles" collection exists
    collection = db_client.get_or_create_collection("news_articles")

    # ✅ Check if collection has any existing articles
    existing_data = collection.get(include=["metadatas"])
    if existing_data and "metadatas" in existing_data and existing_data["metadatas"]:
        print(f"📂 Found {len(existing_data['metadatas'])} existing articles in ChromaDB.")
    else:
        print("⚠️ No articles found in ChromaDB. Starting fresh.")

    # ✅ Print a status message
    print("✅ ChromaDB Initialized. Collection 'news_articles' is ready.")

    # ✅ Scraper logic
    save_json = os.getenv("SAVE_JSON", "True").lower() == "true"
    scraper = NewsScraper(api_key=API_KEY, save_json=save_json)

    # ✅ Run async function safely
    try:
        asyncio.run(scraper.fetch_articles())
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            print("⚠️ Event loop closed unexpectedly. Restarting loop...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(scraper.fetch_articles())

    # Close Playwright safely
    try:
        asyncio.run(scraper.close_browser())
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            print("⚠️ Event loop already closed while shutting down Playwright.")

    # ✅ Save all articles to DB at the end
    scraper.finalize_scraping()



# To run the scraper
#
# In gitbash: 
# 
# pip install aiohttp newspaper3k beautifulsoup4 unstructured html5lib lxml fake-useragent python-dotenv chromadb certifi Pillow playwright brotli
#
# If there's any unstructured errors, try running this again:
# pip install unstructured html5lib lxml 
#
#
# Run command:
# python data_collect.py
#
# Or with your own API Key
# python data_collect.py --api-key YOUR_API_KEY
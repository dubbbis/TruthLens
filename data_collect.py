import os
import json
import asyncio
import aiohttp
from datetime import datetime
from fake_useragent import UserAgent
from newspaper import Article
from bs4 import BeautifulSoup
from unstructured.partition.html import partition_html

## Set the article amount here
MAX_ARTICLES = 50


API_KEY = "356bb7cd80f02083d604ba6ba1dfadd8"

# ✅ Setup Directories & Constants
NEWS_DIR = "NEWS_FILES"
os.makedirs(NEWS_DIR, exist_ok=True)

BASE_URL = f"http://api.mediastack.com/v1/news?access_key={API_KEY}&countries=us&limit={MAX_ARTICLES}"
ua = UserAgent()

paywalled_domains = {"nytimes.com", "washingtonpost.com", "theatlantic.com", "bloomberg.com"}

def is_paywalled(url):
    return any(domain in url for domain in paywalled_domains)

## Note: We could use a txt file to make a list of paywalled sites too

# ✅ Asynchronous Content Extraction
async def extract_full_text(session, url):
    """Extracts article content using newspaper3k, Unstructured, and BeautifulSoup asynchronously."""
    try:
        headers = {'User-Agent': ua.random}
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

# ✅ Fetch Articles Asynchronously
async def fetch_articles(base_url):
    """Fetches news articles and extracts content asynchronously."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(base_url) as response:
                if response.status != 200:
                    print(f"🚨 Failed to fetch news: {response.status}")
                    return []

                news_data = await response.json()
                articles = news_data.get("data", [])[:MAX_ARTICLES]  # MediaStack uses "data"

            tasks = []
            articles_list = []

            for i, article in enumerate(articles):
                url = article.get("url", "")
                if not url or is_paywalled(url):
                    print(f"🚫 Skipping paywalled article: {url}")
                    continue

                print(f"🔍 [{i+1}/{MAX_ARTICLES}] Processing: {url}")
                tasks.append(extract_full_text(session, url))

                articles_list.append({
                    "title": article.get("title", "Unknown title"),
                    "url": url,
                    "published_date": article.get("published_at", "Unknown date"),
                    "source_name": article.get("source", "Unknown source"),
                    "author": article.get("author", "Unknown author"),
                    "category": article.get("category", "Unknown category"),
                })

            full_texts = await asyncio.gather(*tasks)
            for i, text in enumerate(full_texts):
                articles_list[i]["content"] = text

            return articles_list

        except Exception as e:
            print(f"❌ Error fetching articles: {str(e)}")
            return []

async def save_articles():
    articles = await fetch_articles(BASE_URL)
    if articles:
        # ✅ Ensure NEWS_FILES directory exists
        os.makedirs(NEWS_DIR, exist_ok=True)

        # ✅ Generate a unique timestamped filename (YYYY-MM-DD_HH-MM-SS)
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"news_{date_str}.json"
        filepath = os.path.join(NEWS_DIR, filename)  # Save inside NEWS_FILES directory

        # ✅ Save JSON file inside NEWS_FILES
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=4)

        print(f"✅ {len(articles)} articles saved in '{filepath}'.")



if __name__ == "__main__":
    try:
        asyncio.get_running_loop().run_until_complete(save_articles())
    except RuntimeError:
        asyncio.run(save_articles())


## To run this file:
#  python data_collect.py
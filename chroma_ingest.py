import os
import json
import chromadb
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlparse
import re


# Checks archive of JSON files to ingest files that haven't entered DB.
# Makes sure there aren't duplicates, checks via distinct URL

class JSONToChromaDB:
    def __init__(self, news_dir="NEWS_FILES", chroma_db_path="./chroma_db", load_all=True):
        """Initialize the JSON to ChromaDB Loader."""
        self.news_dir = news_dir
        self.chroma_db_path = chroma_db_path
        self.load_all = load_all  # Toggle to load all files or only today's
        self.client = None
        self.collection = None
        self.existing_hashes = set()  # ✅ Store existing article hashes for fast duplicate checking

        # ✅ Initialize ChromaDB
        self._init_chromadb()

    def _init_chromadb(self):
        """Initialize ChromaDB client and collection."""
        if not os.path.exists(self.chroma_db_path):
            print("⚠️ ChromaDB instance not found. Creating a new one...")
            os.makedirs(self.chroma_db_path)
        else:
            print("✅ ChromaDB instance found. Using existing database.")

        self.client = chromadb.PersistentClient(path=self.chroma_db_path)
        collection_name = "news_articles"

        try:
            self.collection = self.client.get_collection(collection_name)
            print(f"✅ Collection '{collection_name}' exists.")
        except Exception:
            print(f"⚠️ Collection '{collection_name}' not found. Creating a new one...")
            self.collection = self.client.create_collection(collection_name)

        # ✅ Load all existing article hashes once at startup
        self._load_existing_hashes()

    def clean_text(self, text):
        """Removes excessive whitespace and HTML artifacts from text."""
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        text = text.replace("\n", " ").strip()  # Remove newlines
        return text

    def process_article(self, article):
        """Processes an article and adds it to ChromaDB."""
        original_url = article.get("url")
        normalized_url = self.normalize_url(original_url)  # ✅ Normalize URL

        title = article.get("title", "Unknown title")
        content = article.get("content", "No content available")
        article_hash = self.generate_article_hash(title, normalized_url, content)  # ✅ Unique identifier

        # ✅ Skip duplicate articles
        if not normalized_url or article_hash in self.existing_hashes:
            return None  # Skip duplicate

        # ✅ Ensure metadata does not contain None values
        metadata = {
            "hash": article_hash,
            "title": title,
            "url": normalized_url,
            "published_date": article.get("published_at", "Unknown date"),
            "source": article.get("source", "Unknown source"),
            "author": article.get("author", "Unknown author"),
            "category": article.get("category", "Unknown category"),
            "language": article.get("language", "Unknown"),  # ✅ Additional fields
            "summary": article.get("description", "No summary available")  # ✅ Include description as summary
        }

        # ✅ Store full document as a combination of content and description
        full_document = f"{self.clean_text(content)}\n\nSummary: {self.clean_text(metadata['summary'])}"

        return (article_hash, metadata, full_document)  # ✅ Return tuple for insertion

    def _load_existing_hashes(self):
        """Loads all existing article hashes from ChromaDB into a set for fast lookups."""
        existing_data = self.collection.get(include=["metadatas"])
        if existing_data and "metadatas" in existing_data:
            self.existing_hashes = {meta["hash"] for meta in existing_data.get("metadatas", []) if "hash" in meta}
            print(f"🔄 Loaded {len(self.existing_hashes)} existing articles from ChromaDB.")

    def get_json_files(self, days=1):
        """Returns JSON files from NEWS_FILES directory based on date range."""
        all_files = [f for f in os.listdir(self.news_dir) if f.endswith(".json")]

        if self.load_all:
            print(f"📂 Loading ALL JSON files ({len(all_files)} found).")
            return all_files

        # Filter files based on date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        date_strings = [cutoff_date.strftime("%Y-%m-%d") for i in range(days)]

        filtered_files = [f for f in all_files if any(date in f for date in date_strings)]
        print(f"📂 Loading JSON files from the last {days} days ({len(filtered_files)} found).")

        return filtered_files


    def normalize_url(self, url):
        """Normalize a URL for consistent duplicate checking."""
        if not url:
            return None
        parsed_url = urlparse(url)
        return parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path  # ✅ Remove query params, standardize format

    def generate_article_hash(self, title, url, content):
        """Generate a unique hash for each article using its title, URL, and content."""
        raw_string = f"{title}{url}{content}"
        return hashlib.sha256(raw_string.encode()).hexdigest()

    def load_json_to_chromadb(self):
        """Loads JSON articles into ChromaDB without duplicates (matching by unique article hash)."""
        json_files = self.get_json_files()
        if not json_files:
            print("⚠️ No JSON files found. Exiting.")
            return

        # ✅ Track added articles count
        added_count = 0
        total_before = len(self.existing_hashes)  # Count before loading

        # ✅ Process each JSON file
        for file in json_files:
            file_path = os.path.join(self.news_dir, file)

            # ✅ Skip empty files before opening
            if os.stat(file_path).st_size == 0:
                print(f"⚠️ Skipping empty file: {file}")
                continue  # Move to the next file

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)  # Load entire JSON file as an object
                        if isinstance(data, list):  
                            articles = data  # If it's a list, assign directly
                        elif isinstance(data, dict) and "articles" in data:  
                            articles = data["articles"]  # If wrapped in an "articles" key
                        else:
                            print(f"⚠️ Unexpected JSON structure in {file}")
                            return
                    except json.JSONDecodeError as e:
                        print(f"❌ Error parsing JSON in {file}: {e}")
                        return


            except Exception as e:
                print(f"❌ Error loading {file}: {e}")
                continue

            # ✅ Batch Process Articles
            new_entries = []  # Stores (id, metadata, document) tuples
            
            for article in articles:
                processed = self.process_article(article)  # Use the function

                if processed:  # If the function returned a valid tuple, add it
                    new_entries.append(processed)


            # ✅ Store articles in ChromaDB in batch
            if new_entries:  # Check if there are any articles to add
                try:
                    # ✅ Ensure safe unpacking (won't crash if empty)
                    filtered_ids, filtered_metadatas, filtered_documents = zip(*new_entries) if new_entries else ([], [], [])

                    # ✅ Ensure the lists have consistent lengths before adding to DB
                    if len(filtered_ids) == len(filtered_metadatas) == len(filtered_documents):
                        self.collection.add(
                            ids=list(filtered_ids),
                            documents=list(filtered_documents),
                            metadatas=list(filtered_metadatas),
                        )
                        print(f"✅ Successfully added {len(filtered_ids)} articles from {file}.")

                        self.existing_hashes.update(filtered_ids)  # ✅ Update existing hashes
                        added_count += len(filtered_ids)
                    else:
                        print(f"❌ Length mismatch detected! Skipping batch from {file}.")

                except Exception as e:
                    print(f"❌ Error adding articles to ChromaDB: {e}")
            else:
                print(f"⚠️ No new articles to add from {file}. Skipping.")

            total_after = len(self.existing_hashes)  # Count after loading

            print(f"\n🎉 Finished loading articles into ChromaDB.")
            print(f"📊 New articles added: {added_count}")
            print(f"📚 Total articles in ChromaDB: {total_after}")




# ✅ Run the script
if __name__ == "__main__":
    json_loader = JSONToChromaDB(news_dir="NEWS_FILES", chroma_db_path="./chroma_db", load_all=True)
    json_loader.load_json_to_chromadb()



## To run this file
#
# pip install chromadb urllib3

#
# python chroma_ingest.py
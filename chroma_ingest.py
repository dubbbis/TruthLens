import os
import json
import chromadb
from datetime import datetime

# ✅ NEWS_FILES Directory
NEWS_DIR = "NEWS_FILES"

# ✅ Toggle: Load ALL files or only today's files
LOAD_ALL_FILES = True  # Change to True if you want to load all JSON files

# ✅ ChromaDB Path
CHROMA_DB_PATH = "chroma_db"

# ✅ Ensure ChromaDB Exists
if not os.path.exists(CHROMA_DB_PATH):
    print("⚠️ ChromaDB instance not found. Creating a new one...")
    os.makedirs(CHROMA_DB_PATH)  
else:
    print("✅ ChromaDB instance found. Using existing database.")

# ✅ Initialize Client & Collection
client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection_name = "news_articles"

try:
    collection = client.get_collection(collection_name)
    print(f"✅ Collection '{collection_name}' exists.")
except Exception:
    print(f"⚠️ Collection '{collection_name}' not found. Creating a new one...")
    collection = client.create_collection(collection_name)



def get_json_files():
    """Returns JSON files from NEWS_FILES directory based on toggle setting."""
    all_files = [f for f in os.listdir(NEWS_DIR) if f.endswith(".json")]
    
    if LOAD_ALL_FILES:
        print(f"📂 Loading ALL JSON files ({len(all_files)} found).")
        return all_files

    # Filter files for today's date
    today_str = datetime.now().strftime("%Y-%m-%d")
    todays_files = [f for f in all_files if today_str in f]
    print(f"📂 Loading today's JSON files only ({len(todays_files)} found).")
    
    return todays_files

def load_json_to_chromadb():
    """Loads JSON articles into ChromaDB without duplicates."""
    json_files = get_json_files()
    if not json_files:
        print("⚠️ No JSON files found. Exiting.")
        return

    # Track added articles count
    added_count = 0
    total_before = len(collection.get().get("ids", []))  # Total in DB before loading

    # ✅ Process each JSON file
    for file in json_files:
        file_path = os.path.join(NEWS_DIR, file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                articles = json.load(f)
        except Exception as e:
            print(f"❌ Error loading {file}: {e}")
            continue

        if not articles:
            print(f"⚠️ Skipping empty file: {file}")
            continue

        # ✅ Process each article
        for article in articles:
            article_id = article.get("url")  # Using URL as a unique ID
            if not article_id:
                continue  # Skip articles with no URL

            existing_ids = collection.get([article_id]).get("ids", [])

            if article_id in existing_ids:
                print(f"🔄 Skipping duplicate article: {article['title']}")
                continue  # Skip duplicate entry

            # ✅ Ensure metadata does not contain None values
            metadata = {
                "title": article.get("title", "Unknown title") or "Unknown title",
                "url": article.get("url", ""),
                "published_date": article.get("published_date", "Unknown date") or "Unknown date",
                "source": article.get("source_name", "Unknown source") or "Unknown source",
                "author": article.get("author", "Unknown author") or "Unknown author",
                "category": article.get("category", "Unknown category") or "Unknown category",
            }

            collection.add(
                ids=[article_id],
                documents=[article.get("content", "No content available") or "No content available"],
                metadatas=[metadata]
            )
            added_count += 1  # Increment added article count
            print(f"✅ Added article: {metadata['title']}")

    total_after = len(collection.get().get("ids", []))  # Total in DB after loading

    print(f"\n🎉 Finished loading articles into ChromaDB.")
    print(f"📊 New articles added: {added_count}")
    print(f"📚 Total articles in ChromaDB: {total_after}")


# ✅ Run the script
if __name__ == "__main__":
    load_json_to_chromadb()

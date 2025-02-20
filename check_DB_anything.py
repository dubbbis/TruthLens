import chromadb

# Connect to ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")  # Ensure this matches your scraper
collection = chroma_client.get_or_create_collection("news_articles")

# Fetch metadata instead of IDs
results = collection.get(include=["metadatas"])

print("🔍 Checking ChromaDB entries...")

if results and "metadatas" in results and results["metadatas"]:
    print(f"✅ Found {len(results['metadatas'])} entries in ChromaDB.")
else:
    print("❌ No entries found in ChromaDB.")

# Additional check: Count total entries
print(f"📊 Total entries in ChromaDB: {collection.count()}")


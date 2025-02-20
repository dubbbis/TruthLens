import os
import json
import chromadb
import requests
import spacy
import numpy as np
import threading
import concurrent.futures
import re
import hashlib
import time
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
from collections import defaultdict
from transformers import pipeline
from dotenv import load_dotenv
from datetime import datetime

# Fact Checking queue for google/wiki because the dictionaries are not thread-safe
# If two threads update them at the same time, data corruption or partial updates may occur
import queue
fact_check_queue = queue.Queue()
wiki_queue = queue.Queue()


import nltk
from nltk.tokenize import sent_tokenize
# Ensure NLTK sentence tokenizer is available

#############   UNCOMMENT TO DOWNLOAD THE FIRST TIME   ##############
#nltk.download("punkt")


# TOGGLE: Set debug mode level
# 0 = No debug
# 1 = Save only one full JSON file
# 2 = Save individual JSON files + one full JSON file
DEBUG_MODE = 2
DEBUG_OUTPUT_DIR = "debug_outputs"

# Ensure debug output directory exists
if DEBUG_MODE > 0 and not os.path.exists(DEBUG_OUTPUT_DIR):
    os.makedirs(DEBUG_OUTPUT_DIR)

# Load environment variables
load_dotenv()
GOOGLE_FACT_CHECK_API_KEY = os.getenv("GOOGLE_FACT_CHECK_API_KEY")

if not GOOGLE_FACT_CHECK_API_KEY:
    raise ValueError("Missing GOOGLE_FACT_CHECK_API_KEY in .env file")

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chromadb_store")
collection = chroma_client.get_or_create_collection("articles")

# Load NLP models
nlp = spacy.load("en_core_web_trf")  # Transformer-based NER model
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")  # Embeddings for dense retrieval
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-12-v2")  # Cross-encoder for claim verification
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
claim_extractor = pipeline("text2text-generation", model="facebook/bart-large-cnn")

def get_current_timestamp():
    """Returns the current timestamp in ISO format."""
    return datetime.utcnow().isoformat()

# Wikipedia API Endpoint
WIKIPEDIA_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# TOGGLE: Choose whether to process ALL or LIMIT processing to a certain amount
LIMIT_MODE = True  # Set to False to process all awaiting documents
AMOUNT = 1  # Change this to 5, 10, 50, etc.

# TOGGLE: Enable debug mode to save RAG outputs as JSON
DEBUG_OUTPUT_DIR = "debug_outputs"

# Ensure debug output directory exists
if DEBUG_MODE and not os.path.exists(DEBUG_OUTPUT_DIR):
    os.makedirs(DEBUG_OUTPUT_DIR)

def fetch_google_fact_check(entities):
    """
    Queries Google Fact Check API for multiple entities in a single request.
    If too many entities exist, it processes them in batches.

    Args:
    - entities (list): List of entity names to fact-check.

    Returns:
    - dict: Fact-check results mapped to entities.
    """
    if not entities:
        return {}

    fact_check_results = {}
    print(f"Fetching Google Fact Check results for {len(entities)} entities...")
    # Split entities into batches (Google API may have character limits)
    BATCH_SIZE = 5  # Adjust batch size as needed
    entity_batches = [entities[i:i + BATCH_SIZE] for i in range(0, len(entities), BATCH_SIZE)]

    for batch in entity_batches:
        query = "+".join(batch)  # Join entities with '+' for batch processing
        url = f"https://factchecktools.googleapis.com/v1alpha1/claims:search?query={query}&key={GOOGLE_FACT_CHECK_API_KEY}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                claims = data.get("claims", [])
                for entity in batch:
                    # Extract relevant claims for each entity in the batch
                    fact_check_results[entity] = [claim for claim in claims if entity.lower() in claim.get("text", "").lower()]
        except Exception as e:
            print(f"Error fetching from Google Fact Check API: {e}")
    print("Google Fact Check API call complete.")
    return fact_check_results  # Dictionary mapping entities to claims

# Function to fetch Wikipedia summary
def fetch_wikipedia_summary(entity):
    print(f"Fetching Wikipedia summary for '{entity}'...")
    url = f"{WIKIPEDIA_API_URL}{entity.replace(' ', '_')}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("extract", "")
    except Exception as e:
        print(f"Error fetching Wikipedia summary for {entity}: {e}")
    print(f"Wikipedia summary retrieved for '{entity}'.")
    return ""

def fetch_from_chromadb(query, retries=3, delay=2):
    """
    Fetch data from ChromaDB with error handling and retry logic.

    Args:
    - query (dict): The query to fetch documents.
    - retries (int): Number of times to retry in case of failure.
    - delay (int): Delay in seconds before retrying.

    Returns:
    - dict: ChromaDB results (empty dict if request fails).
    """
    for attempt in range(retries):
        try:
            results = collection.get(where=query)
            if results and results.get("documents"):
                return results
            else:
                print(f"⚠️ Warning: No documents found for query: {query}")
                return {}
        except Exception as e:
            print(f"Error fetching from ChromaDB (Attempt {attempt+1}/{retries}): {e}")
            time.sleep(delay * (2 ** attempt))  # Exponential backoff
    
    print("Critical: Failed to fetch from ChromaDB after multiple attempts.")
    return {}  # Return an empty dictionary to prevent script failure




# Multi-Hop Fact Checking (First Wikipedia → Then Fact-Check API)
def multi_hop_fact_checking(entities):
    """
    Performs multi-hop fact-checking by first retrieving Wikipedia summaries
    and then passing them to Google Fact Check API in batches.

    Args:
    - entities (list): List of entities to fact-check.

    Returns:
    - dict: Combined fact-check results for all entities.
    """
    if not entities:
        return {}

    wikipedia_summaries = {entity: fetch_wikipedia_summary(entity) for entity in entities}
    refined_queries = [summary if summary else entity for entity, summary in wikipedia_summaries.items()]
    
    # Perform batch fact-checking using refined queries
    fact_check_results = fetch_google_fact_check(refined_queries)

    # Rank fact-checking results if available
    ranked_fact_checks = {}
    for entity, claims in fact_check_results.items():
        ranked_fact_checks[entity] = rank_fact_checks(claims, entity)

    return ranked_fact_checks  # Dictionary with ranked results


def rank_fact_checks(fact_check_results, query):
    scores = cross_encoder.predict([(query, claim) for claim in fact_check_results])
    ranked_claims = [claim for _, claim in sorted(zip(scores, fact_check_results), reverse=True)]
    return ranked_claims


# Function to extract and filter meaningful entities
def extract_entities(text):
    doc = nlp(text)
    filtered_entities = [ent.text for ent in doc.ents if ent.label_ in {"ORG", "GPE", "PERSON", "PRODUCT"}]
    return list(set(filtered_entities))  # Remove duplicates

# BM25 Retrieval
def compute_bm25_rankings(documents, query):
    tokenized_docs = [doc.split() for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)
    tokenized_query = query.split()
    scores = bm25.get_scores(tokenized_query)
    ranked_docs = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in ranked_docs]

# Dense Retrieval
def compute_dense_rankings(documents, query):
    query_embedding = embedding_model.encode(query)
    doc_embeddings = embedding_model.encode(documents)
    similarities = (doc_embeddings @ query_embedding.T).tolist()
    ranked_docs = sorted(zip(documents, similarities), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in ranked_docs]

# Reciprocal Rank Fusion (Combines BM25 & Dense Retrieval)
def reciprocal_rank_fusion(bm25_results, dense_results, k=60):
    scores = defaultdict(float)
    for rank, doc in enumerate(bm25_results):
        scores[doc] += 1 / (rank + k)
    for rank, doc in enumerate(dense_results):
        scores[doc] += 1 / (rank + k)
    return sorted(scores, key=scores.get, reverse=True)

print(f"Running hybrid search for similar articles related to article...")
# Hybrid Search Function
def hybrid_search(query, documents, mode="hybrid"):
    """
    Perform hybrid document retrieval using BM25 and/or Dense Retrieval.

    Parameters:
    - query (str): The search query.
    - documents (list of str): List of documents to search in.
    - mode (str): 
        - "bm25" → BM25-only retrieval
        - "dense" → Dense embeddings retrieval
        - "hybrid" (default) → Combine BM25 & Dense using Reciprocal Rank Fusion

    Returns:
    - List of retrieved documents sorted by relevance.
    """

    bm25_results, dense_results = [], []

    # ✅ Run BM25 if "bm25" or "hybrid" mode is selected
    if mode in {"bm25", "hybrid"}:
        bm25_results = compute_bm25_rankings(documents, query)

    # ✅ Run Dense Retrieval if "dense" or "hybrid" mode is selected
    if mode in {"dense", "hybrid"}:
        dense_results = compute_dense_rankings(documents, query)

    # ✅ If Hybrid mode, combine results using Reciprocal Rank Fusion
    if mode == "hybrid":
        return reciprocal_rank_fusion(bm25_results, dense_results)

    # ✅ Otherwise, return results from the selected method
    return bm25_results if mode == "bm25" else dense_results

# Function to compute sentiment analysis using BERT
import numpy as np
from nltk.tokenize import sent_tokenize

def sentiment_analysis(text, chunk_size=512):
    """
    Process sentiment analysis on large text by splitting it into sentence-based chunks
    and computing a weighted average sentiment score.

    Parameters:
    - text (str): The input text.
    - chunk_size (int): The maximum length of each chunk (default: 512 for BERT models).

    Returns:
    - float: The weighted sentiment score across all chunks.
    """

    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_length = 0
    chunk_lengths = []  # Stores sentence count per chunk for weighted averaging

    # Split text into chunks
    for sentence in sentences:
        sentence_length = len(sentence)
        
        if current_length + sentence_length > chunk_size:
            chunks.append(" ".join(current_chunk))
            chunk_lengths.append(len(current_chunk))  # Track sentence count
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))
        chunk_lengths.append(len(current_chunk))

    sentiment_scores = []

    # Analyze sentiment for each chunk
    for chunk in chunks:
        result = sentiment_analyzer(chunk)
        label = result[0]["label"]
        score = result[0]["score"]
        numerical_score = score if label == "POSITIVE" else -score
        sentiment_scores.append(numerical_score)

    # Compute weighted average sentiment score
    if sentiment_scores:
        weighted_avg_sentiment = np.average(sentiment_scores, weights=chunk_lengths)
    else:
        weighted_avg_sentiment = 0  # Default value if no sentiment scores are computed

    return weighted_avg_sentiment



# Function to compute credibility score
def compute_credibility_score(fact_check_results, wikipedia_summaries, linguistic_features):
    score = 0
    if fact_check_results:
        score += 50  # Boost score if fact-checking sources validate the data
    if wikipedia_summaries:
        score += 20  # Additional credibility boost for Wikipedia presence
    if linguistic_features["sentiment_score"] > 0.2:
        score += 15
    if linguistic_features["named_entity_density"] > 0.3:
        score += 15
    return min(score, 100)  # Ensure max credibility score is 100

def generate_text_hash(text):
    """Generate a hash of the text content for deduplication purposes."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# Function to process and enrich articles
def process_article(doc_id, text):
    print(f"Processing article: {doc_id}")
    

    # Extract metadata
    print(f"Extracting entities from article {doc_id}...")
    entities = extract_entities(text)

     # Ensure all retrieved articles have timestamps
    search_results = fetch_from_chromadb(
        where={
            "$or": [
                {"status": {"$eq": "ready"}}, # Documents explicitly marked "ready"
                {"status": {"$exists": False}}, # Documents missing "status" field
                {"status": {"$eq": None}}  # Explicitly handle NULL values
            ]
        },
        limit=AMOUNT
    )

        # Ensure timestamps exist or assign a default one
    valid_results = []

    for res in search_results.get("matches", []):  # Ensure "matches" exists
        metadata_list = res.get("metadatas", [])  # Get "metadatas", default to empty list
        
        if metadata_list:  # Ensure the list is not empty
            metadata = metadata_list[0]  # Get the first metadata dictionary
            
            # Assign a timestamp if missing
            if "timestamp" not in metadata or metadata["timestamp"] is None:
                metadata["timestamp"] = get_current_timestamp()
            
            valid_results.append(res)
        else:
            print(f"⚠️ Skipping entry: Missing metadata in search result {res.get('id', 'Unknown')}")

    # Sort manually by timestamp (now all documents have a timestamp)
    sorted_results = sorted(valid_results, key=lambda x: x["metadatas"][0]["timestamp"], reverse=True)


    # Extract document texts for similarity search
    search_texts = [res["documents"][0] for res in sorted_results] if sorted_results else []

    # Choose retrieval mode dynamically
    # This saves time because you don't always need to run both
    RETRIEVAL_MODE = "auto"  # Options: "bm25", "dense", "hybrid", "auto"

    if RETRIEVAL_MODE == "auto":
        if len(search_texts) > 50:
            retrieval_mode = "bm25"
        elif len(text.split()) > 300:
            retrieval_mode = "dense"
        else:
            retrieval_mode = "hybrid"
    else:
        retrieval_mode = RETRIEVAL_MODE

    # Run optimized Hybrid Search
    related_articles = hybrid_search(text, search_texts, mode=retrieval_mode) if search_texts else []

    print(f"🔎 Running multi-hop fact-checking for article {doc_id}...")
    # Initialize empty dictionaries to store results (critical fix)
    fact_check_results = {}
    wikipedia_summaries = {}

    def fetch_fact_checks(entities):
        """ Fetches fact-check results for given entities in a thread-safe manner. """
        for entity in entities:
            try:
                results = multi_hop_fact_checking([entity])  # Fetch fact-check results
                fact_check_queue.put((entity, results))  # Store results in thread-safe queue
            except Exception as e:
                print(f"⚠️ Error fetching fact-check results for {entity}: {e}")
                fact_check_queue.put((entity, []))  # Store empty list in case of failure



    def fetch_wikipedia(entities):
        """ Fetches Wikipedia summaries in a thread-safe manner using a queue. """
        for entity in entities:
            try:
                summary = fetch_wikipedia_summary(entity)  # Fetch Wikipedia summary
                wiki_queue.put((entity, summary))  # Store result in thread-safe queue
            except Exception as e:
                print(f"Error fetching Wikipedia summary for {entity}: {e}")
                wiki_queue.put((entity, ""))  # Store empty string in case of failure


    # Run API calls in parallel, passing `entities`
    fact_check_thread = threading.Thread(target=fetch_fact_checks, args=(entities,))
    wiki_thread = threading.Thread(target=fetch_wikipedia, args=(entities,))
    # Start the threads
    fact_check_thread.start()
    wiki_thread.start()
    # After completing, they join
    fact_check_thread.join()
    wiki_thread.join()

    # Extract fact-check results from queue
    while not fact_check_queue.empty():
        entity, facts = fact_check_queue.get()
        fact_check_results[entity] = facts  # Store safely in dictionary

    # Extract Wikipedia summaries from queue
    while not wiki_queue.empty():
        entity, summary = wiki_queue.get()
        wikipedia_summaries[entity] = summary  # Store safely in dictionary


    # Compute linguistic insights
    print(f"Running sentiment analysis for article {doc_id}...")
    sentiment_score = sentiment_analysis(text)
    named_entity_density = len(entities) / max(len(text.split()), 1)
    linguistic_features = {
        "sentiment_score": sentiment_score,
        "named_entity_density": named_entity_density
    }
    credibility_score = compute_credibility_score(fact_check_results, wikipedia_summaries, linguistic_features)

    # Generate a unique hash for the document's content
    text_hash = generate_text_hash(text)

    # Check if an entry with the same content hash already exists
    existing_entries = fetch_from_chromadb(where={"text_hash": text_hash})

    if existing_entries and existing_entries.get("documents"):
        print(f"Duplicate detected for document {doc_id}. Skipping addition.")
        return {doc_id: "Duplicate detected, skipping processing."}

    # Retrieve original metadata if available
    existing_metadata = fetch_from_chromadb(where={"id": doc_id})
    original_metadata = existing_metadata["metadatas"][0] if existing_metadata and "metadatas" in existing_metadata else {}

    print(f"Merging original data with enriched data...")
    # Merge original metadata with enriched data
    enriched_metadata = {
        **original_metadata,
        "original_text": text,
        "text_hash": text_hash,  # Store the hash to prevent future duplicates
        "entities": entities,
        "related_articles": related_articles,
        "fact_check_results": fact_check_results,
        "wikipedia_summaries": wikipedia_summaries,
        "sentiment_score": sentiment_score,
        "credibility_score": credibility_score,
        "status": "ready"
    }
    print(f"Storing processed article {doc_id} in ChromaDB...")
    def save_to_chromadb(doc_id, text, enriched_metadata, retries=3, delay=2):
        """
        Save a document to ChromaDB with error handling and retry logic.

        Args:
        - doc_id (str): The document ID.
        - text (str): The document text.
        - enriched_metadata (dict): Metadata to store.
        - retries (int): Number of retry attempts.
        - delay (int): Delay in seconds before retrying.

        Returns:
        - bool: True if successful, False if failed.
        """
        for attempt in range(retries):
            try:
                collection.add(ids=[doc_id], documents=[text], metadatas=[enriched_metadata])
                print(f"Successfully saved document {doc_id} to ChromaDB.")
                return True
            except Exception as e:
                print(f"Error saving to ChromaDB (Attempt {attempt+1}/{retries}): {e}")
                time.sleep(delay * (2 ** attempt))  # Exponential backoff
        
        print(f"Critical: Failed to save document {doc_id} to ChromaDB after multiple attempts.")
        return False  # Return False so the caller knows the save operation failed

    # Store updated metadata in ChromaDB
    print(f"Storing processed article {doc_id} in ChromaDB...")
    save_to_chromadb(doc_id, text, enriched_metadata)

    print(f"Article {doc_id} processed and marked as 'ready'.")

    # Save individual JSON file if DEBUG_MODE is set to 2
    if DEBUG_MODE == 2:
        safe_doc_id = re.sub(r'[^a-zA-Z0-9_-]', '_', doc_id)  # Ensure filename is safe
        debug_file_path = os.path.join(DEBUG_OUTPUT_DIR, f"{safe_doc_id}.json")

        with open(debug_file_path, "w", encoding="utf-8") as f:
            json.dump(enriched_metadata, f, indent=4, ensure_ascii=False)

        print(f"Saved individual debug JSON for {doc_id}: {debug_file_path}")

    return {doc_id: enriched_metadata}  # Return processed entry


# Function to process all unprocessed articles
def process_articles():
    print("Fetching unprocessed articles from ChromaDB...")
    results = fetch_from_chromadb(
    where={
        "$or": [
            {"status": {"$eq": None}},   # Check for NULL/missing
            {"status": {"$eq": "raw"}},  # Explicitly fetch "raw"
            {"status": {"$exists": False}},  # ChromaDB-specific way to check missing fields
        ]
    }
)


    if not results or not results["documents"]:
        print("No new articles to process.")
        return

    doc_count = len(results["documents"])
    print(f"Found {len(results['documents'])} articles to process.")
    num_to_process = AMOUNT if LIMIT_MODE else doc_count
    print(f"Processing {num_to_process} out of {doc_count} pending articles...")

    processed_entries = {}

    # Use ThreadPoolExecutor for parallel processing

    '''
    NB:
    If the tasks become CPU-intensive, switch to ProcessPoolExecutor (but for now, threading is better due to I/O-heavy tasks).
    Increase max_workers if your system can handle more simultaneous threads.
    '''
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:  # Adjust max_workers as needed
        future_to_doc = {
            executor.submit(process_article, doc_id, text): doc_id
            for doc_id, text in zip(results["ids"][:num_to_process], results["documents"][:num_to_process])
        }

        for future in concurrent.futures.as_completed(future_to_doc):
            doc_id = future_to_doc[future]
            try:
                processed_entry = future.result()
                processed_entries.update(processed_entry)
            except Exception as e:
                print(f"Error processing article {doc_id}: {e}")

    print("🏁 All articles processed!")
    print(f"📁 Debug output saving to {DEBUG_OUTPUT_DIR}...")

    # Write a single JSON file with all processed data
    # Generate timestamped filename for debugging
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    full_debug_filename = f"rag_processed_{timestamp}.json"
    static_debug_filename = "rag_processed_entries.json"

    # Determine the correct file path
    debug_file_path = os.path.join(DEBUG_OUTPUT_DIR, full_debug_filename) if DEBUG_MODE == 2 else os.path.join(DEBUG_OUTPUT_DIR, static_debug_filename)

    # Save full debug JSON file if DEBUG_MODE is set to 1 or 2
    if DEBUG_MODE in {1, 2}:
        with open(debug_file_path, "w", encoding="utf-8") as f:
            json.dump(processed_entries, f, indent=4, ensure_ascii=False)

        print(f"Saved full debug JSON file: {debug_file_path}")



if __name__ == "__main__":
    process_articles()

## To run this:
#
# In Gitbash:
#
# pip install chromadb requests spacy numpy rank-bm25 sentence-transformers transformers python-dotenv nltk
#
# python -m spacy download en_core_web_trf
#
# Important!! ****  If you haven’t downloaded the spaCy language model, you need to.
# 
# To run on GPU:
#
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
#
# To run file:
# python RAG_processing.py
## FakeBuster Planning

MVP Creation

MVP:
Due: Feb 21

Dates and work finished:
* Feb 12 - planning + API Integration
* Feb 13 - continued API and testing with LLM - deepseek-r1
* Feb 14 - API collection improvements and testing: vector store of json data, start RAG and preprocessing

* Feb 17
* Feb 18
* Feb 19
* Feb 20
* Feb 21 -- MVP DEMO NEEDED


## Checklist

1. Set up LLM Integration using API

Ollama
* We downloaded deepseek-r1 and have it running

a. DEEPSEEK
 * Running it locally

b. LLAMA
 * Need to test this!! <-- either next week or the week after 


2. Build API Framework
    - Connect to news sites, gather data for each article
        - title, url, content (text) 
        - full text from each article is needed
        - next week: figure out how many articles saved in news.json


3. Build RAG
    - Storage: Store news content in a vector database (ChromaDB).
    - Retrieve related context when analyzing a new news article.
    - Pass retrieved context + new query to your local LLM Deepseek-R1 for enhanced fact-checking.
    - Still need to optimize linguistic analysis and include sections for crosschecking and factchecking
    - Sentiment Analysis solidify and explain the metrics (so we understand) also so we make sure LLM understand


4. Build Fake News Detection Prompts
    - Use new cleaned_news.json to send to LLM 
    - cleaned_news.json has text along with summary and linguistic_analysis data


4. Testing and Iteration
    - Create Fake News from GPT and feed that into the model
        format is news.json

5. Think about scaling the storage of the news.json 
    - to allow for more storage and some organize

6. Build a Front End (optional)


## DUE Feb 21st - MVP for Demo

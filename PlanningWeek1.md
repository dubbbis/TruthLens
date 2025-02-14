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






















ORIGINAL PROJECT TIMELINE



   
## Further explanation and details:

1. Set Up the LLM Integration (Day 1-2):

   API Integration: Use a pre-existing API like OpenAI, Hugging Face, or any other LLM provider you want to work with. Set up a simple API endpoint that accepts prompts (you can start with basic fake news detection prompts, like "Is this news article fake?").
   Basic Testing: Test a variety of sample prompts and fine-tune the structure if needed. This will help ensure the LLM gives useful, relevant outputs before investing time into complex workflows.

Time Estimate: 1-2 days to set up the API, integrate with the LLM, and test basic prompts.

2. Basic API Framework (Day 2-3):

   Build a lightweight API (using frameworks like Flask, FastAPI, or Django) that receives text input (e.g., news article content) and sends it as a prompt to the LLM.
   Design endpoints for sending text and receiving responses from the LLM. At this point, you don’t need a full-fledged interface—just ensure that the LLM can be queried with a basic prompt, and responses are returned in a usable format.

Time Estimate: 1-2 days to create the skeleton API that can accept inputs and return LLM responses.

3. Initial Fake News Detection Prompts (Day 3-4):

   Create some basic prompts and try different variations to test how the LLM can identify or flag fake news.
       Example: "Analyze the following news article for signs of being fake: [article text here]."
       Example: "Does the following news report seem credible? [article text here]."
       Focus on the LLM’s ability to provide binary or confidence-based outputs, such as “True/False” or a credibility score.
   Fine-tune the prompts to ensure they elicit relevant and useful responses.

Time Estimate: 1-2 days to build initial fake news detection prompts and refine them for useful results.

4. Simplified Frontend (Optional) (Day 4-5):

   If you have time, you can add a simple frontend for interacting with the API. This could be a simple web form where users paste news article text and get responses back from the LLM.
   Alternatively, if you’re focusing on backend functionality, you could skip this step for now and rely on direct API calls for testing purposes.

Time Estimate: 1 day (optional, depends on team capacity).

5. Testing and Iteration (Day 5-7):

   Run multiple tests with different types of content (news articles) and refine the prompts as needed. Test edge cases like misleading headlines, satire articles, or biased content to see how the LLM handles these.
   Evaluate the LLM’s responses to check for consistency and usefulness. You may need to adjust the prompts or handle responses more intelligently based on the LLM’s outputs (e.g., thresholding confidence scores for fake news detection).

Time Estimate: 2-3 days to test the system end-to-end and refine it based on results.



# Long Term Goals

Building a fake news detector using web scraping, RAG (retrieval-augmented generation) to transform data, and leveraging an LLM like Deepseek or Llama is an ambitious but potentially feasible project. The difficulty and time needed will depend on several factors, such as the complexity of the data pipeline, your team's experience, and the specific requirements of the fake news detector. Here’s a breakdown of the major tasks involved, their complexity, and some strategies to make this feasible within your 15-20 workday timeframe:
Key Steps in the Process:

    1. Web Scraping for Content:
        Tasks Involved:
            Identify target websites that typically publish news articles or content you want to scrape (e.g., news sites, blogs, etc.).
            Write or use a web scraping tool to extract relevant data (e.g., BeautifulSoup or Scrapy for Python).
            Clean and normalize the data (i.e., removing ads, navigation bars, non-relevant information).
        Complexity: Moderate to high. Building a reliable and scalable scraper might take time, especially if you're scraping multiple websites with different structures.
        Time Estimate: 3-5 days (depending on the number and variety of websites you're scraping).

    2. Data Storage and Management:
        Tasks Involved:
            Store scraped content in a structured format (e.g., a database like PostgreSQL, Elasticsearch, or simple file storage like JSON or CSV).
            Ensure that the data is updated regularly and can be queried efficiently.
        Complexity: Low to moderate. You can use existing solutions (like a relational database or document store).
        Time Estimate: 2-3 days (for setting up and testing).

    3. RAG Pipeline for Data Transformation:
        Tasks Involved:
            Build a retrieval system that can efficiently query and retrieve relevant information from your scraped data (e.g., using Elasticsearch, FAISS, or a custom search index).
            Design the transformation of this retrieved data into prompts suitable for an LLM (e.g., converting scraped data into context-rich inputs for fake news detection).
        Complexity: High. You will need to implement an effective retrieval mechanism and fine-tune how the data is used to prompt the LLM.
        Time Estimate: 5-7 days (for building, testing, and debugging).

    4. Integration with an LLM (e.g., Deepseek or Llama):
        Tasks Involved:
            Set up the API or model interface for LLMs.
            Feed the prompts into the model and interpret its responses (e.g., detecting fake news signals from the LLM output).
            Fine-tune the model or apply post-processing to improve the results.
        Complexity: Moderate. You will need to understand the LLM API, work on prompt engineering, and handle responses.
        Time Estimate: 3-5 days.

    5. Fake News Detection Logic:
        Tasks Involved:
            Implement logic to analyze the LLM responses and detect fake news indicators (e.g., inconsistent information, misleading headlines, etc.).
            Create a confidence scoring system for identifying fake news.
        Complexity: High. This might involve some research into fake news detection and possibly machine learning.
        Time Estimate: 3-5 days.

    6. Testing and Validation:
        Tasks Involved:
            Test the system end-to-end with different types of news articles.
            Ensure the scraper is working reliably and the LLM is producing useful outputs.
            Validate the accuracy of the fake news detector.
        Complexity: High. Testing in real-world scenarios and validating the results is crucial, especially for a fake news detection model.
        Time Estimate: 2-4 days.

## Feasibility in 15-20 Workdays:

    Challenges: The project involves several steps that are complex on their own (scraping, data storage, RAG, LLM integration, fake news detection). Some parts may require iterating on designs and tuning, especially when it comes to data retrieval and LLM responses.

    Team Considerations: With a team of two, the workload can be manageable, but it depends on experience. One person could focus on scraping and data storage while the other works on the RAG and LLM integration. If your team has experience with these technologies (web scraping, machine learning, APIs), the timeline is realistic, but you'll need to manage the complexity by narrowing down the scope or using existing tools/libraries where possible.

    Optimizing the Process:
        Use pre-built libraries and APIs where possible (for example, Scrapy for scraping, Elasticsearch for search, Hugging Face API for LLMs).
        Consider limiting the number of websites or the depth of your scraper to save time.
        Use an existing fake news detection model and fine-tune it if possible, instead of building the fake news detector from scratch.

## Final Assessment:

    Timeframe: Realistically, with a focused and skilled team, you can get a basic version of the system working within 15-20 workdays, but it will be a challenge to make it production-ready or highly accurate. Prioritize key features and aim for a basic prototype first.

    Next Steps:
        Break down tasks into smaller milestones.
        Use agile methods to iterate quickly, focusing on MVP functionality for each component (scraping, RAG, LLM integration).

    In summary, the project is doable but will require focused effort, especially in efficiently integrating all components and ensuring the fake news detector is reliable.

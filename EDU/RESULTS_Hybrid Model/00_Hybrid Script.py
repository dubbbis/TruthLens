import requests
import pandas as pd
from bs4 import BeautifulSoup
import ollama
import json

# NewsAPI setup
API_KEY = "d306519089ed41f798067a3c686b6226"  # Replace with your actual API key
NEWS_API_URL = "https://newsapi.org/v2/everything"

def get_news_json(query, sources="bbc-news,cnn", page_size=5):
    """Fetch news articles from NewsAPI and return JSON."""
    params = {
        "q": query,
        "sources": sources,
        "pageSize": page_size,
        "apiKey": API_KEY
    }
    
    response = requests.get(NEWS_API_URL, params=params)
    
    if response.status_code != 200:
        return {"error": f"Error fetching news: {response.status_code}"}
    
    data = response.json()
    articles = [
        {
            "title": article["title"],
            "content": article["content"],
            "url": article["url"],
            "publishedAt": article["publishedAt"]
        }
        for article in data.get("articles", [])
    ]
    
    return articles  # Return structured data

def get_full_article(url):
    """Scrape the full content of an article using BeautifulSoup."""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract article content
    # This is just an example and may need adjustment depending on the website structure
    paragraphs = soup.find_all('p')
    article_content = ' '.join([para.get_text() for para in paragraphs])
    
    return article_content

# Define the prompt template
prompt_template = """
Analyze the following news article and determine its credibility. 
Provide a score from 0-100% (0 = completely false, 100 = completely true).
Also, explain why the rating was given.

News Article: {news}
"""

# Define test cases
test_cases = [
    {
        "name": "Test Case 1",
        "input": "COVID-19 vaccine safety",  # Your query to NewsAPI
    },
    # Add more test cases as needed
]

# List to store article data
article_data = []

# Run the test cases and fetch news articles
for test in test_cases:
    print(f"\n🔹 Testing: {test['name']}")
    
    # Get news data using NewsAPI
    news_articles = get_news_json(test["input"])
    
    # If there are articles returned, process each one
    if isinstance(news_articles, list) and news_articles:
        for article in news_articles:
            article_title = article["title"]
            article_url = article["url"]
            article_content = article["content"] or get_full_article(article_url)  # Use full article if content is missing
            
            # Store the article info in the article_data list
            article_data.append({
                "title": article_title,
                "content": article_content,
                "url": article_url,
                "publishedAt": article["publishedAt"]
            })
            
            # Process the content with the Ollama model
            prompt = prompt_template.format(news=article_content)
            response = ollama.chat(
                model="deepseek-r1", 
                messages=[{"role": "user", "content": prompt}]
            )
            
            print("📢 Model Response:\n", response['message']['content'])
    
    else:
        print("📢 No relevant articles found or error fetching data.")

# Convert the article data into a DataFrame for easy handling
df = pd.DataFrame(article_data)

# Clean the data (e.g., remove rows with NULL values)
df_clean = df.dropna()

# Display the cleaned DataFrame
print("\n📊 Cleaned Article DataFrame:")
print(df_clean)
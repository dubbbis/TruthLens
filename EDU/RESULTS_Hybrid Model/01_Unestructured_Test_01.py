import requests
from unstructured.partition.html import partition_html
import ollama
import pandas as pd

# Define the prompt for the LLM model
prompt_template = """
Analyze the following news article and determine its credibility. 
Provide a score from 0-100% (0 = completely false, 100 = completely true).
Also, explain why the rating was given.

News Article: {news}
"""

# Function to extract clean article content using Unstructured.io
def get_clean_article(url):
    """Extracts the main content of a news article from a URL using Unstructured.io"""
    response = requests.get(url)
    if response.status_code != 200:
        return None

    # Process the HTML with Unstructured.io
    elements = partition_html(text=response.text)
    
    # Join only narrative text paragraphs
    article_text = "\n".join([str(el) for el in elements if el.category == "NarrativeText"])

    return article_text

# URL of the news article to analyze
article_url = "https://www.bbc.com/news/live/c24728zpp70t"

# Get the clean content of the news article
article_content = get_clean_article(article_url)

# If the article could not be extracted, terminate the process
if not article_content:
    print("❌ Could not extract content from the article.")
    exit()

# Pass the content to the LLM model for fake news verification
prompt = prompt_template.format(news=article_content)
response = ollama.chat(
    model="deepseek-r1", 
    messages=[{"role": "user", "content": prompt}]
)

# Display the model's response
print("📢 Model Response:\n", response['message']['content'])

# Organize in a DataFrame
article_data = [{
    "title": "BBC News - Example Title",  # You can extract it from Unstructured.io if needed
    "content": article_content,
    "url": article_url
}]

df = pd.DataFrame(article_data)
print("\n📊 Cleaned Article DataFrame:")
print(df)

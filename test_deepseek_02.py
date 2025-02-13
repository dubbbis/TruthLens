import ollama
import requests
from bs4 import BeautifulSoup

# Define test cases
test_cases = [
    {
        "name": "Basic Fake News Detection",
        "input": "The Earth is flat and NASA has been hiding the truth for decades.",
    },
    {
        "name": "Reliable News Example",
        "input": "The World Health Organization confirms that vaccines are safe and effective for preventing diseases.",
    },
    {
        "name": "Biased News Example",
        "input": "Democrats are ruining the economy with their reckless spending policies.",
    },
    {
        "name": "Fact-Check Request",
        "input": "Is it true that 5G towers spread COVID-19?",
    },
    {
        "name": "Satirical News Test",
        "input": "New study finds that coffee is now considered a superfood that extends life by 50 years.",
    }
]

def scrape_news(url):
    """Extracts the main content from a news article URL."""
    response = requests.get(url)
    if response.status_code != 200:
        return f"Error: Unable to fetch the article. Status Code: {response.status_code}"
    
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = soup.find_all('p')  # Extracting text from <p> tags
    article_text = '\n'.join([p.get_text() for p in paragraphs])
    
    return article_text[:2000]  # Limit text length to avoid token overflow

def preprocess_text(text):
    """Basic text cleaning for preprocessing."""
    return ' '.join(text.split())  # Remove extra whitespace

def retrieve_facts():
    """Simulate retrieval of relevant facts for RAG."""
    return "NASA has confirmed that the Earth is an oblate spheroid based on satellite data and observations."

def analyze_news(news_text):
    """Analyze news credibility."""
    cleaned_text = preprocess_text(news_text)
    facts = retrieve_facts()  # Basic RAG simulation
    
    prompt_template = """
    Analyze the following news article and determine its credibility.
    Provide a score from 0-100% (0 = completely false, 100 = completely true).
    Also, explain why the rating was given.
    
    News Article: {news}
    Relevant Facts: {facts}
    """
    
    prompt = prompt_template.format(news=cleaned_text, facts=facts)
    response = ollama.chat(model="deepseek-r1", messages=[{"role": "user", "content": prompt}])
    
    return response['message']['content']

# Run the test cases
for test in test_cases:
    print(f"\n🔹 Testing: {test['name']}")
    response = analyze_news(test["input"])
    print("📢 Model Response:\n", response)

# Example usage with a URL
news_url = "https://www.bbc.com/news/live/c4g97971rwnt"
scraped_news = scrape_news(news_url)
if "Error" not in scraped_news:
    print("\n🔹 Testing Web Scraped Article")
    response = analyze_news(scraped_news)
    print("📢 Model Response:\n", response)

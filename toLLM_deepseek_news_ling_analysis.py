import json
import ollama

# Load the processed news articles
with open("linguistic_news.json", "r", encoding="utf-8") as f:
    news_articles = json.load(f)

# Deepseek-R1 Prompt Template
prompt_template = """
You are an AI news analyst. Your task is to determine whether a news article is FAKE or TRUE.
Analyze the linguistic and factual credibility of this article.

News Article:
{news}

---

🔹 TASK:
1️⃣ Provide a **5-sentence** explanation of whether this article is **fake or true**.
2️⃣ Assign a **credibility score (0-100%)** based on reliability, grammar, and content accuracy.

🎯 **Scoring Guide:**
- **0-20%** → Highly Fake
- **21-50%** → Likely Fake
- **51-75%** → Possibly True
- **76-100%** → Highly True
"""

# Select a few test cases (first 3 articles)
test_cases = [{"name": f"Article {i+1}", "input": article["content"]} for i, article in enumerate(news_articles[:3])]

# Run the test cases
for test in test_cases:
    print(f"\n🔹 Testing: {test['name']}")
    
    # Fill the prompt template with the article
    prompt = prompt_template.format(news=test["input"])
    
    # Send request to Deepseek-R1
    response = ollama.chat(
        model="deepseek-r1", 
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Extract and display response
    print("📢 Model Response:\n", response["message"]["content"])


## Use to run:
## python deepseek_news_ling_analysis.py

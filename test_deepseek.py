import ollama

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

# Define the prompt template
prompt_template = """
Analyze the following news article and determine its credibility. 
Provide a score from 0-100% (0 = completely false, 100 = completely true).
Also, explain why the rating was given.

News Article: {news}
"""

# Run the test cases
for test in test_cases:
    print(f"\n🔹 Testing: {test['name']}")
    prompt = prompt_template.format(news=test["input"])
    
    response = ollama.chat(
        model="deepseek-r1", 
        messages=[{"role": "user", "content": prompt}]
    )
    
    print("📢 Model Response:\n", response['message']['content'])

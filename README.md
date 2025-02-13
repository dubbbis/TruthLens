# Fake News Detection with Machine Learning

**Project Description**

In this project, a Machine Learning model will be developed to detect fake news using the Fake and Real News Dataset from Kaggle ([https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset](https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset)). This dataset contains news articles labeled as real or fake, allowing us to train and evaluate classification algorithms.

## **Objective**

The main objective is to build a model capable of distinguishing between real and fake news with high accuracy. This will help analyze patterns in the language used in each category and explore Natural Language Processing (NLP) approaches.


## Methodology

- **Data Exploration and Cleaning:** Analyzing dataset characteristics, removing irrelevant data, and preprocessing the text.

- **Text Analysis:** Tokenization, stopword removal, lemmatization, and vectorization (TF-IDF, Word Embeddings, etc.).

- **Model Training:** Comparing different classification algorithms (Logistic Regression, Random Forest, SVM, Neural Networks).

- **Evaluation and Optimization:** Using metrics such as accuracy, recall, and F1-score to measure model performance.

- **Deployment and Interpretation:** Implementing the model and analyzing the most relevant features for classification.

## Expected Results

* Identify the most relevant text features for detecting fake news.
* Develop a model with high accuracy in classifying real and fake news.
* Explore the impact of different preprocessing techniques and machine learning models.



### Set up your Environment

Please make sure you have forked the repo and set up a new virtual environment.

The added [requirements file](requirements.txt) contains all libraries and dependencies we need to execute the NLP notebooks.

**`Note:`**

- If there are errors during environment setup, try removing the versions from the failing packages in the requirements file. silicon shizzle.
- In some cases it is necessary to install the **Rust** compiler for the transformers library.
- make sure to install **hdf5** if you haven't done it before.

 - Check the **rustup version**  by run the following commands:
    ```sh
    rustup --version
    ```
    If you haven't installed it yet, begin at `step_1`. Otherwise, proceed to `step_2`.


### **`macOS`** type the following commands : 

- `Step_1:` Update Homebrew and install **rustup** and **hdf5** by following commands:

    ```BASH
    brew install rustup
    rustup-init
    ```
    Then press ```1``` for the standard installation.
    
    Then we can go on to install hdf5:
    
    ```BASH
     brew install hdf5
    ```

  Restart Your Terminal and then check the **rustup version**  by running the following commands:
     ```sh
    rustup --version
    ```
 
- `Step_2:` Install the virtual environment and the required packages by following commands:

  > NOTE: for macOS with **silicon** chips (other than intel)
    ```BASH
    pyenv local 3.11.3
    python -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements_silicon.txt
    ```
  > NOTE: for macOS with **intel** chips
  ```BASH
    pyenv local 3.11.3
    python -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

    
### **`WindowsOS`** type the following commands :

- `Step_1:` Install **rustup**  by following :
  
  1. Visit the official Rust website: https://www.rust-lang.org/tools/install.
  2. Download and run the `rustup-init.exe` installer.
  3. Follow the on-screen instructions and choose the default options for a standard installation.
  4. Then press ```1``` for the standard installation.
 
     
    Then we can go on to install hdf5:

    ```sh
     choco upgrade chocolatey
     choco install hdf5
    ```
    Restart Your Terminal and then check the **rustup version**  by running the following commands:
  
     ```sh
    rustup --version
    ```

- `Step_2:` Install the virtual environment and the required packages by following commands.

   For `PowerShell` CLI :

    ```PowerShell
    pyenv local 3.11.3
    python -m venv .venv
    .venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    ```

    For `Git-bash` CLI :
  
    ```BASH
    pyenv local 3.11.3
    python -m venv .venv
    source .venv/Scripts/activate
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    ```



### Ollama and Deepseek install

## 🚀 Setup Guide

### **1️⃣ Create Virtual Environment**
```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# OR
source .venv/Scripts/activate  # Windows
```

### 2️⃣ Install Dependencies

pip install ollama langchain beautifulsoup4 requests scrapy pandas chromadb faiss-cpu sentence-transformers tiktoken

### 3️⃣ Install & Run Deepseek LLM

# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh  # Mac/Linux
# Download Deepseek Model
ollama pull deepseek-r1
# Test the model
ollama run deepseek-r1 "What is fake news?"

### 4️⃣ Quick Test in Python

import ollama

response = ollama.chat(model="deepseek", messages=[{"role": "user", "content": "Analyze this news: The moon landing was fake. How credible is this?"}])
print(response['message']['content'])
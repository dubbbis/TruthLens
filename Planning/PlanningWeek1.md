# 📰 FakeBuster Planning  

## 🎯 MVP Creation  
**MVP Due:** **Feb 21**  

### **✅ Dates and Work Finished**
- **Feb 12** - Planning + API Integration  
- **Feb 13** - Continued API and testing with LLM (Deepseek-R1)  
- **Feb 14** - API collection improvements, vector store of JSON data, start RAG and preprocessing  

### **📅 Upcoming Tasks**
- **Feb 17** - TBD  
- **Feb 18** - TBD  
- **Feb 19** - TBD  
- **Feb 20** - TBD  
- **Feb 21** - 🎤 **MVP Demo Needed!**  

---

## **✅ Checklist**

### **1️⃣ Set Up LLM Integration (Without Using API)**
#### **Ollama**
- ✅ **Deepseek-R1 downloaded and running**  

#### **LLM Testing**
- ✅ **Deepseek-R1:** Running locally  
- 🔹 **Llama:** **Needs testing** (Planned for next week or the following week)  

---

### **2️⃣ Build API Framework**
- ✅ **Connect to news sources & gather article data**  
    - We are using **Mediastack API**  
    - **Usage limit:** 100 requests per month → Keep this in mind during testing  
    - **Solution:** Create a second account if we need more requests  
- ✅ **Fields needed:** `title`, `URL`, `full-text content`  
- 🔹 **Next Week:** Determine how many articles are saved in `news.json`  
    - 📌 **To-Do:** Figure out **ChromaDB** and how to store large amounts of articles  

---

### **3️⃣ Build RAG (Retrieval-Augmented Generation)**
- ✅ **Retrieval:** Fetch related context for analyzing new news articles  
    - Using `news.json` data gathered via API framework  
    - Initial RAG testing has been done ✅  
    - **Needs major improvements!** We also need **evaluation metrics** to track progress  
    - **🔹 Advice Needed:** How to effectively test and improve RAG?  

#### **🔹 Improvements Needed:**  
- ✅ **Fact-Checking:** Pass retrieved context + new query to **Deepseek-R1**  
- ✅ **Cross-Checking:** Pass retrieved context + new query to **Deepseek-R1**  
    - **Further testing required** to refine accuracy  
- ✅ **Storage:** Store news content in **ChromaDB** (vector database)  
- ✅ **Optimize & expand linguistic analysis**  
    - Create **`linguistic_news.json`** with enhanced fact-checking details  
- ✅ **Refine Sentiment Analysis**  
    - Clearly document metrics for **better LLM interpretation**  

---

### **4️⃣ Build Fake News Detection Prompts**
- ✅ Use **`linguistic_news.json`** as input for LLM  
- ✅ Ensure **text, summaries, and linguistic analysis** are included in the dataset  

---

### **5️⃣ Testing & Iteration**
- ✅ **Generate Fake News using GPT** and feed it into the model  
- ✅ Format generated fake news in **`news.json`** for structured testing  

#### **🔹 Improvements Needed:**  
- **Put fake news through RAG and cleaning pipeline** before testing with LLM  
- **Compare old vs. new model results** → Set up structured evaluations  
- **Start tracking model performance over time** (logs, accuracy trends, etc.)  
- **Expected Outcome:** We should have **strong test data** ready for the MVP demo  

---

### **6️⃣ Scaling & Storage Optimization**
- 🔹 Plan how to **store & manage a larger dataset of news articles efficiently**  
- 🔹 Consider organizing **long-term storage solutions** for future expansion  

---

### **7️⃣ (Optional) Build a Front-End**
- 🔹 If time permits, develop a **UI for querying & displaying fact-checked articles**  

---

## **🚀 MVP Deadline: Feb 21st**
🎯 **Goal:** **Fully functional Fake News Detector**  
🎤 **Deliverable:** Live demo + system walkthrough  

🔥 **Next Steps:**  
1️⃣ Continue improving **RAG retrieval**  
2️⃣ Finalize **LLM testing & fact-checking prompts**  
3️⃣ **Prepare for the MVP demo!**  

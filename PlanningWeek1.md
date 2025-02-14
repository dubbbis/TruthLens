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

### **1️⃣ Set Up LLM Integration without using API**
#### **Ollama**
- ✅ **Deepseek-R1 downloaded and running**  

#### **LLM Testing**
- 🔹 **Deepseek-R1:** Running locally  
- 🔹 **Llama:** **Needs testing** (Planned for next week or the following week)  

---

### **2️⃣ Build API Framework**
- ✅ **Connect to news sources & gather article data**  
  - **Fields needed:** `title`, `URL`, `full text content`  
- 🔹 **Next Week:** Determine how many articles are saved in `news.json`  

---

### **3️⃣ Build RAG (Retrieval-Augmented Generation)**
- ✅ **Retrieval:** Fetch related context for analyzing new news articles  
- ✅ **Fact-Checking:** Pass retrieved context + new query to **Deepseek-R1**  
    - Further testing needed here.
- 🔹 **Improvements Needed:** 
  - **Storage:** Store news content in **ChromaDB** (vector database)  
  - **Optimize linguistic analysis** (improve cross-checking & fact-checking)  
    - Make **`linguistic_news.json`** with enhanced information
  - **Refine sentiment analysis** (document metrics clearly for model interpretation)  

---

### **4️⃣ Build Fake News Detection Prompts**
- ✅ Use **`linguistic_news.json`** as input for LLM  
- ✅ Ensure **text, summaries, and linguistic analysis** are included in the dataset  

---

### **5️⃣ Testing & Iteration**
- ✅ **Generate Fake News using GPT** and feed it into the model  
- ✅ Format generated fake news in **`news.json`** for structured testing
    - 🔹 **Improvements Needed:** 
        - Need to put this all through RAG and cleaning pipeline, then off to the LLM for testing
        - Work out the best way to compare old and new model results, start running and tracking them
        - Will be able to deliver lots of good data already at MVP demo

---

### **6️⃣ Scaling & Storage Optimization**
- 🔹 Plan how to **store & manage more news articles efficiently**  
- 🔹 Consider organizing **long-term storage solutions**  

---

### **7️⃣ (Optional) Build a Front-End**
- 🔹 If time permits, develop a **UI for querying & displaying fact-checked articles**  

---

## **🚀 MVP Deadline: Feb 21st**
🎯 **Goal:** **Fully functional Fake News Detector**  
🎤 **Deliverable:** Live demo + system walkthrough  

🔥 **Next steps:** Continue improving RAG retrieval, finalize LLM testing, and prepare for the MVP demo!  

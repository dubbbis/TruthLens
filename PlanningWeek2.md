# 🚀 FakeBuster MVP Plan (Feb 17-21)

## 🎯 MVP Creation  
**MVP Due:** **Feb 21**  

### **✅ Dates and Work Finished**
- **Feb 12** - Planning + API Integration  
- **Feb 13** - Continued API and testing with LLM (Deepseek-R1)  
- **Feb 14** - API collection improvements, vector store setup, start RAG and preprocessing  

---

## 🗓 **Updated Plan for Next Week (Feb 17-21)**  

### **📅 Feb 17 - Finalizing RAG System**
- ✅ **Store news articles in ChromaDB** (vector DB)  
- ✅ **Retrieve & test context relevance**  
- ✅ **Test RAG pipeline with Deepseek-R1**  
- ✅ Ensure **retrieved context improves LLM fact-checking**  
- 🔹 **Optimize how ChromaDB stores large amounts of articles**  
- 🔹 **Begin tracking retrieval quality & relevance metrics**  

---

### **📅 Feb 18 - Model Testing (LLM: Llama vs. Deepseek-R1)**
- ✅ **Test Llama for comparison**  
- ✅ **Refine Fake News Detection Prompts**  
- ✅ Test **Deepseek-R1 with RAG-enhanced context**  
- ✅ **Solidify Sentiment Analysis Metrics** (explain & document for LLM understanding)  
- 🔹 **Determine if Deepseek-R1 or Llama performs better for fake news detection**  
- 🔹 **Improve fact-checking prompts for better accuracy**  

---

### **📅 Feb 19 - Fake News Detection & Model Evaluation**
- ✅ **Finalize Fake News Detection pipeline**  
- ✅ Optimize **linguistic analysis** (fact-checking + cross-checking)  
- ✅ **Create fake news samples** from GPT & test detection  
- ✅ Ensure model **assigns proper credibility scores**  
- 🔹 **Test performance on real vs. fake news articles & compare output**  
- 🔹 **Expand testing dataset for more robust evaluation**  

---

### **📅 Feb 20 - System Testing, Scaling & Data Storage**
- ✅ **Run full system test** (API → RAG → LLM Analysis)  
- ✅ **Optimize storage of `news.json`** (scaling strategy)  
- ✅ **Identify & fix weak points**  
- ✅ (Optional) **Front-end work if time permits**  
- 🔹 **Consider automated daily news collection & storage**  
- 🔹 **Improve article storage structure (metadata, indexing, etc.)**  

---

### **📅 Feb 21 - 🎤 MVP Demo Preparation**
- ✅ **Prepare slides & documentation**  
- ✅ **Run live demo**  
- ✅ **Final debugging & last-minute fixes**  
- 🔹 **Prepare case studies/examples to showcase model results**  
- 🔹 **Ensure reproducibility (so others can use/test the system)**  

---

## **📝 Checklist of Tasks**

### **🔹 1. LLM Integration**
- ✅ **Deepseek-R1 Running Locally**  
- ✅ **Test Llama** (Completed Feb 18)  
- 🔹 **Choose final model for Fake News Detection (Deepseek-R1 vs. Llama)**  

### **🔹 2. API Framework**
- ✅ **Connect to news sites & collect full text**  
- ✅ **Determine how many articles are saved in `news.json`**  
- 🔹 **Improve `news.json` scaling for long-term use**  

### **🔹 3. Build & Optimize RAG**
- ✅ **Store articles in ChromaDB**  
- ✅ **Optimize linguistic analysis**  
- ✅ **Refine sentiment analysis & metrics**  
- 🔹 **Track RAG retrieval effectiveness & adjust filtering methods**  

### **🔹 4. Fake News Detection**
- ✅ **Use `linguistic_news.json` for LLM input**  
- ✅ **Test model with fake news examples**  
- ✅ **Ensure LLM understands credibility scoring**  
- 🔹 **Add confidence scoring & justification explanations**  

### **🔹 5. Storage & Scaling**
- ✅ **Optimize `news.json` for larger datasets**  
- ✅ **Organize data storage for long-term use**  
- 🔹 **Consider additional storage methods if data exceeds limits**  

### **🔹 6. (Optional) Front-End Work**
- 🔹 **UI for querying fact-checked articles** (only if time allows)  

---

## **🚀 Next Steps**
1️⃣ **Finalize RAG improvements & retrieval testing (Feb 17-18)**  
2️⃣ **Choose the best LLM model for Fake News Detection (Feb 18-19)**  
3️⃣ **Refine Fake News Detection & Sentiment Analysis (Feb 19-20)**  
4️⃣ **Complete full system testing & prepare for MVP Demo (Feb 20-21)**  

🔥 **This updated plan ensures a well-tested, optimized FakeBuster MVP for Feb 21! 🚀**  
Let me know if you need further refinements! 🔥  

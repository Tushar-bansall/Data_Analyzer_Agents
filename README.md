

# 🔍 **AI Business Analyst**

Turn any CSV or Excel dataset into **clean insights, trends, and business answers** using multi-agent reasoning (CrewAI) + OpenAI/Gemini fallback.

---

## 🚀 Overview

**AI Business Analyst** is a smart data-analysis assistant that allows users to upload datasets and ask business questions.
The backend automatically:

* Reads & cleans the dataset
* Detects data issues
* Extracts trends
* Answers user-defined business questions
* Generates human-interpretable insights
* Creates smart charts (optional feature)
* Uses **Gemini as fallback** if OpenAI runs into quota/limit errors

The frontend is a simple, clean UI built with **HTML + Tailwind** to upload files and view results.

---

## ✨ Features

### 🔹 **1. Upload CSV or Excel**

Drag & drop or select `.csv`, `.xlsx`, `.xls`.

### 🔹 **2. Ask Any Business Question**

Examples:

* *“What drives customer churn?”*
* *“Which department has highest attrition?”*
* *“What KPIs matter most?”*

### 🔹 **3. AI-Generated Insights**

The backend returns:

* ✔️ Summary
* ✔️ Data issues
* ✔️ Trends
* ✔️ Answer to your question

Formatted cleanly and point-wise.

### 🔹 **4. CrewAI Multi-Agent System**

Three agents:

* **Data Cleaner** – detects inconsistencies
* **Data Analyst** – discovers trends
* **Business Expert** – answers your question

### 🔹 **5. Smart LLM Fallback**

If OpenAI hits `429 insufficient_quota`:

* System **automatically switches to Google Gemini**
* Ensures the analysis never fails

### 🔹 **6. Simple, Modern Frontend**

Tailwind UI shows:

* Summary
* Data Issues
* Trends
* Answer

Charts optional (removed in your version).

---

## 🏗️ Architecture

```
Frontend (HTML + Tailwind + JS)
       ↓
FastAPI Backend
       ↓
CrewAI Agents (Cleaner, Analyst, Business Expert)
       ↓
OpenAI → (fallback to Gemini)
```

---

## 📦 Installation

### 1️⃣ Clone the Repository

```sh
git clone https://github.com/USERNAME/agenticai.git
cd agenticai
```

### 2️⃣ Create Virtual Environment

```sh
python -m venv .venv
source .venv/Scripts/activate   # Windows
```

### 3️⃣ Install Requirements

```sh
pip install -r requirements.txt
```

### 4️⃣ Set Environment Variables

Create `.env`:

```
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
```

### 5️⃣ Start Backend

```sh
uvicorn backend.main:app --reload --port 3000
```

### 6️⃣ Open Frontend

Open `frontend/index.html` in your browser.

---

## 📁 Project Structure

```
agenticai/
│
├── backend/
│   ├── main.py
│   ├── crew_builder.py
│   ├── agents/
│   └── chart_utils.py
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css (optional)
│
├── requirements.txt
└── README.md
```

---

## 🧠 How It Works

### ✔ Step 1 — File Read

CSV/Excel → Pandas DataFrame

### ✔ Step 2 — AI Team is Formed

CrewAI spawns:

* Data Cleaner Agent
* Data Analyst Agent
* Business Expert Agent

### ✔ Step 3 — LLM Processing

If **OpenAI works → use OpenAI**
If **429 error → fallback to Gemini**

### ✔ Step 4 — Unified Response

The system extracts:

* Summary
* Data Issues
* Trends
* Question Answer

Returned as a structured JSON.

---

## 🖥️ Frontend Features

* Clean UI
* File upload
* Question input
* Loading status indicator
* Organized output sections

---

## 🔧 Requirements

* Python 3.10+
* FastAPI
* CrewAI
* OpenAI SDK
* Google Gemini SDK
* Pandas

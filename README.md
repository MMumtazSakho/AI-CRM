# AI-CRM with Sentiment Analysis

A simple web-based CRM application built with Flask that automatically analyzes customer sentiment using a pre-trained Hugging Face model.

## 🚀 Live Demo

**Access the live application here:**
**[https://ai-crm-demo-1098550132960.asia-southeast2.run.app](https://ai-crm-demo-1098550132960.asia-southeast2.run.app)**

---
**⚠️ Important Demo Notes:**

1.  **Cold Start:** This app is deployed on Google Cloud Run and scales to zero. The **first load will be slow** (approx. 1-2 minutes) as the server needs to "wake up" and load the AI model into memory. After this initial start, the app will be fast.
2.  **Temporary Database:** The demo uses a temporary SQLite database. All data will be **erased** whenever the server goes idle and shuts down.

---

## ✨ Features

* **Lead Management:** Full CRUD (Create, Read, Update, Delete) functionality for customer leads.
* **AI Sentiment Analysis:** Automatically classifies customer `notes` as "Positive", "Negative", or "Neutral" upon creation or update.
* **Analytics Dashboard:** A dynamic bar chart visualizes the proportion of sentiments.
* **Date Filtering:** Filter the sentiment dashboard by a specific date range.
* **Bulk Upload:** Batch upload leads from a `.csv` or `.xlsx` file.

## 🛠️ Tech Stack

* **Backend:** Flask (Python)
* **Database:** SQLite
* **AI Model:** Transformers (Hugging Face) - `tabularisai/multilingual-sentiment-analysis`
* **Frontend:** Vanilla JavaScript (for modal and chart logic), HTML, CSS
* **Data Processing:** Pandas (for file uploads)
* **Charting:** Chart.js
* **Deployment:** Docker, Google Cloud Run

## Local Setup and Installation

Follow these steps to run the project locally.

### 1. Prerequisites

* Python 3.9+
* Git

### 2. Clone Repository

```bash
git clone https://github.com/MMumtazSakho/AI-CRM.git
cd AI-CRM
````

### 3\. (IMPORTANT) Download the AI Model

This project is configured to load the AI model from a local folder named `model`. You must download it manually (it is not tracked by Git).

1.  Go to the model page: [tabularisai/multilingual-sentiment-analysis](https://huggingface.co/tabularisai/multilingual-sentiment-analysis)
2.  Click on the **"Files and versions"** tab.
3.  Download all the key files (e.g., `model.safetensors`, `config.json`, `tokenizer.json`, etc.).
4.  Create a folder named `model` in the root of the project directory.
5.  Place all the downloaded model files inside this `model` folder.

Your project structure should look like this:

```
AI-CRM/
├── model/
│   ├── config.json
│   ├── model.safetensors
│   └── (other model files...)
├── templates/
│   └── index.html
├── app.py
├── requirements.txt
└── .gitignore
```

### 4\. Setup Virtual Environment and Install Dependencies

```bash
# Create a virtual environment
python -m venv venv

# Activate the environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS/Linux:
# source venv/bin/activate

# Install the required libraries
pip install -r requirements.txt
```

### 5\. Run the Application

```bash
python app.py
```

Open your browser and go to `http://127.0.0.1:5000/`.

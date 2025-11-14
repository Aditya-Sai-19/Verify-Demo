# 📄 ForgeryShield – Document Forgery Detection System

ForgeryShield is an intelligent **Streamlit-based application** that helps detect potential document forgery using:

- **Metadata Analysis**
- **Error Level Analysis (ELA)**
- **Template-Based Element Verification (OpenCV)**
- **Automated PDF → Image Processing**

This tool assists in identifying manipulated documents such as certificates, legal papers, ID cards, and signed documents.

## 🚀 Features

### ✅ **1. Metadata Analysis**
Extracts metadata from PDF-converted images and flags suspicious tags related to editing software like:
- Photoshop
- GIMP
- Adobe tools

### ✅ **2. Error Level Analysis (ELA)**
Performs pixel-level manipulation detection by:
- Re-saving the image
- Highlighting anomalies
- Producing an ELA heatmap

### ✅ **3. Template Matching for Forgery Detection**
Allows users to upload a **trusted template element** such as:
- Signature
- Stamp
- Government seal

The system auto-corrects swapped inputs, resizes the template, and highlights mismatch probability.

### ✅ **4. Final Anomaly Scoring**
A weighted system determines a PASS/FAIL verdict for document authenticity.

---

## 📁 Folder Structure

```
ForgeryShield/
│── temp_files/              
│── app.py                   
│── requirements.txt         
│── README.md                
```

---

## 📦 Installation

### 1️⃣ Install Requirements
```bash
pip install -r requirements.txt
```

### 2️⃣ Run Application
```bash
streamlit run app.py
```

---

## 🛠 Tech Stack

| Component | Technology |
|----------|------------|
| Frontend | Streamlit |
| Backend | Python |
| Image Processing | OpenCV, PIL, NumPy |
| PDF Processing | PyMuPDF |

---

## 🙌 Credits
Developed by **Aditya SAI**.

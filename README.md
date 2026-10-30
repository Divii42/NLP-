# NEXUS NER — NLP Named Entity Recognition Extractor

A Streamlit application for extracting named entities and exploring linguistic information using spaCy.

## Features
- Named entity extraction for people, organizations, locations, dates, money, percentages, and more
- Highlighted entity visualization
- Entity counts and frequency statistics
- Token analysis, lemma, POS, fine-grained tag, dependency, stop-word flag, and entity label
- Upload `.txt`, `.pdf`, and `.docx` files
- Export entities, tokens, and summary as CSV
- Glassmorphism-inspired dark dashboard

## Requirements
- Windows 10/11
- Python 3.10 or 3.11 recommended
- Internet connection for first-time package and language-model installation

## Windows installation

Open PowerShell in this project folder.

### 1. Create a virtual environment
```powershell
py -3.10 -m venv .venv
```

If you have Python 3.11 instead, use:
```powershell
py -3.11 -m venv .venv
```

### 2. Activate it
```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this only for the current terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Download the spaCy English model
```powershell
python -m spacy download en_core_web_sm
```

### 5. Start the app
```powershell
python -m streamlit run app.py
```

Streamlit should open a browser tab. If it does not, open:
http://localhost:8501

## Quick test
Use the sample paragraph preloaded in the app:
> Microsoft CEO Satya Nadella visited New Delhi on 15 January 2025. The company announced an investment of $3 billion in India and expects the project to create 2,500 jobs. Researchers from Chandigarh University will collaborate with teams in Bengaluru.

Expected labels may include PERSON, ORG, GPE, DATE, MONEY, and CARDINAL. Model results can vary; NER is not perfect.

## Supported files
- `.txt`: UTF-8, UTF-8 BOM, or Latin-1 text
- `.pdf`: text-based PDFs (scanned image-only PDFs need OCR, which is not included)
- `.docx`: Word documents, including basic table text

## Troubleshooting
**`No module named streamlit`**  
Activate `.venv` and run `pip install -r requirements.txt`.

**`Can't find model 'en_core_web_sm'`**  
Activate `.venv`, then run `python -m spacy download en_core_web_sm`.

**PowerShell says scripts are disabled**  
Run the temporary execution policy command in step 2, then activate again.

**PDF produces no text**  
The PDF may be scanned or image-only. Convert it to a text-searchable PDF or copy its text into the input box.

## Notes
- The default model is trained primarily for English. It may mislabel ambiguous names and may not perform well on every language or domain.
- Text is processed by the local Python app; this code does not send uploaded text to a custom remote server.
- This is an educational project, not a production-grade entity extraction service.

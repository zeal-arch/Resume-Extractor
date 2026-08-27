# Resume Information Extraction System

A rule-based, NLP-assisted system for extracting structured data from PDF and DOCX resumes without relying on external LLMs or APIs.

---

## Features

| Field | Type |
|---|---|
| Full Name | Mandatory |
| Email Address | Mandatory |
| Phone Number | Mandatory |
| Skills | Mandatory |
| Education (degree, institution, year, score) | Bonus |
| Work Experience | Bonus |
| LinkedIn Profile URL | Bonus |
| GitHub Profile URL | Bonus |

---

## Tech Stack

| Library | Purpose |
|---|---|
| `PyMuPDF` (`pymupdf`) | Layout-aware PDF extraction (multi-column, sidebar) |
| `pypdf` | Fallback linear PDF extraction |
| `python-docx` | DOCX text and hyperlink extraction |
| `spaCy` (`en_core_web_sm`) | Named entity recognition (person names) |
| `FastAPI` + `uvicorn` | REST API backend |
| `re` | Regex-based extraction of emails, phones, links |

---

## How It Works

```
PDF / DOCX file
      │
      ▼
┌─────────────────────────────────┐
│  Layout-Aware Parser            │  ← PyMuPDF bounding-box extraction
│  (column detection, XY-cut)     │     preserves visual reading order
└──────────────┬──────────────────┘
               │ plain text
               ▼
┌─────────────────────────────────┐
│  Extractor Pipeline             │
│  name  │ email │ phone          │
│  skills│ edu   │ experience     │
│  linkedin  │  github            │
└──────────────┬──────────────────┘
               │ JSON
               ▼
         REST API  /api/extract
```

**Multi-column handling**: PyMuPDF block bounding boxes are used to detect vertical whitespace gaps and assign text blocks to columns. Full-width elements (headers, footers) are interleaved in correct reading order.

**Name extraction**: 4-pass heuristic — top 10 lines → top 50 lines → spaCy NER → single-word fallback. Rejects section headers, job titles, language names, and possessives.

---

## Prerequisites

- Python 3.10+
- pip

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/zeal-arch/Resume-Extractor.git
cd Resume-Extractor
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download the spaCy language model

```bash
python -m spacy download en_core_web_sm
```

---

## Running the API Server

```bash
uvicorn app:app --reload
```

The server starts at **http://127.0.0.1:8000**

- **UI**: open `http://127.0.0.1:8000` in your browser
- **API docs**: `http://127.0.0.1:8000/docs`

---

## API Usage

### `POST /api/extract`

Upload a resume file (PDF or DOCX) and receive structured JSON.

**cURL example:**

```bash
curl -X POST http://127.0.0.1:8000/api/extract \
  -F "file=@path/to/resume.pdf"
```

**Response:**

```json
{
  "name": "Zealous Sebastian",
  "email": "zealoussebastian464@gmail.com",
  "phone": "+91 74834 47726",
  "skills": ["React", "Next.Js", "Python", "Node.Js", "Sql", "Git"],
  "education": [
    {
      "degree": "M.Sc. Computer Science",
      "institution": "Kristu Jayanti University, Bengaluru",
      "year": "2024"
    }
  ],
  "experience": [
    "Freelance Full-Stack Developer",
    "2024 - Present"
  ],
  "linkedin": "linkedin.com/in/zealous-sebastian",
  "github": "github.com/zeal-arch"
}
```

---

## Project Structure

```
Resume-Extractor/
├── app.py                    # FastAPI application entry point
├── main.py                   # CLI entry point (batch mode)
├── requirements.txt
├── approach_note.md          # Methodology and design decisions
├── data/
│   └── sample_resumes/       # Test resumes (PDF + DOCX)
├── static/
│   └── index.html            # Frontend UI
└── src/
    ├── parsers/
    │   ├── __init__.py       # extract_text() dispatcher
    │   ├── layout_extractor.py  # PyMuPDF geometry engine
    │   ├── pdf_parser.py     # PDF parsing + link extraction
    │   ├── docx_parser.py    # DOCX parsing + link extraction
    │   └── normalizer.py     # Ligature fix, CamelCase split
    └── extractors/
        ├── __init__.py       # extract_all() pipeline
        ├── name.py           # 4-pass name extraction
        ├── email.py          # Email regex
        ├── phone.py          # Phone regex
        ├── skills.py         # Skill dictionary matching
        ├── education.py      # Education section parser
        ├── experience.py     # Experience section parser
        ├── links.py          # LinkedIn / GitHub URL extractor
        └── helpers.py        # Shared constants and utilities
```

---

## Supported File Types

| Format | Extension | Engine |
|---|---|---|
| PDF (text-based) | `.pdf` | PyMuPDF → pypdf fallback |
| Word Document | `.docx` | python-docx |

> **Note:** Scanned/image PDFs (no embedded text layer) return empty results. OCR support is not included.

---

## Batch CLI Mode

To process a folder of resumes and output JSON files:

```bash
python main.py --input_dir data/sample_resumes --output_dir data/outputs
```

---

## Limitations

- Scanned image PDFs require OCR (not included).
- Highly stylised resumes that embed text as vector graphics may extract partially.
- Education and experience parsing relies on section header detection and may miss non-standard headings.

---

## License

MIT

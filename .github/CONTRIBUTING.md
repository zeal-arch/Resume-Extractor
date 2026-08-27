# Contributing to Resume Information Extraction System

Thank you for taking the time to contribute! This project is a heuristic-based resume parser — contributions that improve extraction accuracy, add edge-case handling, or clean up code are very welcome.

---

## Before You Start

- Read the [README](../README.md) to understand the overall architecture.
- Read [`approach_note.md`](../approach_note.md) to understand the methodology and known limitations.
- Check existing [Issues](../../issues) before opening a new one.

---

## Setting Up the Dev Environment

```bash
git clone https://github.com/zeal-arch/Resume-Extractor.git
cd Resume-Extractor
python -m venv .venv
.\.venv\Scripts\activate        # Windows
source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## How to Contribute

### Reporting a Bug

Open an issue and include:
- The resume layout type (single-column / two-column / sidebar)
- The field that extracted incorrectly (name, phone, etc.)
- The expected vs actual output
- The resume file if it does not contain real personal data

### Improving Extraction

The extractor pipeline lives in `src/extractors/`. Each field has its own module:

| Module | Responsible for |
|---|---|
| `name.py` | 4-pass name extraction |
| `email.py` | Email regex |
| `phone.py` | Phone regex |
| `skills.py` | Skill dictionary + matching |
| `education.py` | Education section parser |
| `experience.py` | Experience section parser |
| `links.py` | LinkedIn / GitHub URL extraction |

To test your changes against all sample resumes, create a quick script:

```python
import json, os
from src.parsers import extract_text
from src.extractors import extract_all

for f in os.listdir("data/sample_resumes"):
    text, uris = extract_text(f"data/sample_resumes/{f}")
    print(json.dumps(extract_all(text, uris), indent=2))
```

### Adding New Skills

Add entries to `_TECH_SKILLS` or `_SKILLS_SPECIAL_CHARS` in `src/extractors/skills.py`.

---

## Code Style

- Python 3.10+, type hints everywhere.
- No external LLMs or paid APIs.
- Keep each extractor module self-contained — no cross-imports between extractors.
- Pre-compile all `re.compile(...)` patterns at module level.

---

## Pull Request Checklist

- [ ] Code runs without errors against `Zeal's_resume.pdf` and at least 2 other resumes.
- [ ] No new dependencies added without updating `requirements.txt`.
- [ ] Docstring updated if the function behaviour changed.
- [ ] No dead/commented-out code left in.

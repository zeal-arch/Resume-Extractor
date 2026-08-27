# Approach, Assumptions, and Limitations

## Approach

The system was deliberately designed to run entirely locally without relying on external LLMs or Generative AI APIs, ensuring maximum data privacy and low latency. The architecture relies on robust geometric parsing combined with established Natural Language Processing (NLP) heuristics:

1. **Layout-Aware Text Extraction (PyMuPDF)**
   Standard PDF extractors (like `pypdf`) suffer from the "word salad" problem on multi-column resumes, scrambling text from left and right sidebars together. We utilized `PyMuPDF` to extract text blocks along with their `(x0, y0, x1, y1)` geometric bounding boxes. By detecting large vertical white-space gaps (`gap_ratio > 0.05`), the parser automatically groups text into visual columns before interleaving full-width headers. This preserves the intended reading order.

2. **Phone Validation via Global Telecom Rules (`phonenumbers`)**
   International phone numbers vary wildly, making pure regex prone to false positives (e.g. matching date ranges like `01/2012 - 04/2019`). We utilized Google's `phonenumbers` library, which relies on a massive offline XML database of global telecom rules to validate and standardize extracted numbers to the E.164 format.

3. **Multi-Pass Name Heuristics & NER (`spaCy`)**
   Extracting names without an LLM is challenging due to layout variations. We implemented a 4-pass system:
   * **Pass 1 & 2:** Scans the top 10 (and then top 50) lines for sequences of 2-4 words that start with uppercase letters and do not contain digits, possessives (e.g. "IBM's"), or match our vocabulary of job titles and section headers.
   * **Pass 3:** If heuristic scanning fails, we fallback to local NER using `spaCy`'s `en_core_web_sm` model to detect `PERSON` entities in the top 50 lines.
   * **Pass 4:** A final fallback for single-word names (sometimes caused by unicode icon parsing errors).

4. **Vocabulary Intersection (Skills)**
   Rather than attempting to guess skills semantically, we rely on a comprehensive, hand-curated vocabulary list (`_TECH_SKILLS`). The text is tokenized, stripped of punctuation, and intersected with our dictionary. This guarantees 0% hallucination for technical skills.

5. **RFC-Practical Email Regex & Annotation Scanning**
   We extract emails using a robust regex pattern that explicitly prevents consecutive dots or leading dots (common OCR errors) while supporting multi-level domains. Additionally, the system parses hidden `mailto:` URIs from PDF metadata to catch emails hidden behind clickable buttons (e.g. "Contact Me").

---

## Assumptions

1. **English Language**: The parser assumes the resume is written in English. Our rejection dictionaries (`_JOB_TITLE_WORDS`), section headers, and `spaCy` NER model are English-specific.
2. **Skill Dictionary**: We assume the target extraction fields are primarily software/tech related. Our dictionary is heavily biased towards languages, frameworks, and cloud infrastructure.
3. **Layout Predictability**: We assume the candidate's name is located somewhere in the top 50 lines of the parsed text flow. 

---

## Limitations

1. **Scanned Documents (Images)**
   If a PDF is a scanned image or rasterized flat file (e.g., JPEG converted to PDF), the system will return `null` for most fields. OCR (Optical Character Recognition) was intentionally omitted to keep dependencies lightweight and processing time under 100ms per resume.
2. **Non-Standard Headers**
   If a candidate uses highly creative or unusual section headers (e.g., "My Journey So Far" instead of "Experience"), the heuristic parser will fail to trigger the block extraction boundaries, causing that section to be missed.
3. **Extremely Complex Vector Graphics**
   Some designer resumes build text using individual vector glyphs rather than continuous text blocks. While `PyMuPDF` handles bounding boxes well, scattered individual letters cannot always be stitched back together cohesively.

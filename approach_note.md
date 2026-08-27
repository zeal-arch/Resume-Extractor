# Approach, Assumptions, and Limitations

## Approach

The system was built without relying on external LLMs or Generative AI APIs, strictly adhering to the assignment requirements. The approach leverages traditional Natural Language Processing (NLP) and rule-based techniques:

1.  **Text Extraction**: We utilize `pypdf` for parsing PDF documents and `docx2txt` for DOCX files. These are robust, standard libraries for basic text extraction.
2.  **Regular Expressions (Regex)**: For highly structured data, regex is the most reliable approach. We use carefully crafted regex patterns to extract:
    *   Email Addresses
    *   Phone Numbers (handling various local and international formats)
    *   LinkedIn Profile URLs
    *   GitHub Profile URLs
3.  **Named Entity Recognition (NER)**: We use the `spaCy` library with its pre-trained small English model (`en_core_web_sm`). To extract the candidate's name, we scan the first few lines of the resume for entities classified as `PERSON`. Since resumes typically start with the candidate's name, this heuristic improves accuracy over scanning the entire document where references or author names might be falsely flagged.
4.  **Keyword Matching (Skills)**: We define a comprehensive dictionary of technical skills. The system tokenizes the resume text and performs word-boundary matching (via Regex) against this dictionary to extract relevant skills.
5.  **Heuristic Rule-Based Parsing (Education & Experience)**:
    *   The system scans the text for common section headers (e.g., "Education", "Work Experience", "Academic Background").
    *   Once inside a section, it applies secondary heuristics (e.g., looking for degree acronyms like "B.Tech", or university names for Education, and date patterns or string lengths for Experience) to isolate the relevant lines.

## Assumptions

1.  **Standard Layouts**: The resumes follow a somewhat standard vertical layout where text flows from top to bottom. Multi-column resumes might result in text extraction where logical blocks are interwoven, which can confuse heuristic parsers.
2.  **English Language**: The parser assumes the resume is written in English, primarily because the `spaCy` model used and the skill/header dictionaries are in English.
3.  **Skill Dictionary Completeness**: The extracted skills are limited to the ones defined in our internal `TECH_SKILLS` dictionary. While comprehensive for common tech roles, very niche or brand-new technologies might be missed if not present in the list.

## Limitations

1.  **Complex Formatting**: Rule-based parsers struggle with complex PDF formats, tables, and unconventional designs. Information embedded in images or complex multi-column layouts might not be extracted correctly by `pypdf`.
2.  **Rigid Section Headers**: If a candidate uses highly creative or unusual section headers (e.g., "My Journey So Far" instead of "Experience"), the heuristic parser will fail to identify the section and might miss the experience data.
3.  **Entity Resolution Ambiguity**: `spaCy`'s pre-trained `PERSON` entity recognizer is not perfect and can sometimes misclassify company names, locations, or uncommon names, especially when devoid of typical sentence context (which is common in resumes).
4.  **Context Understanding**: Unlike LLMs, this system does not *understand* context. It extracts lines based on rules. For example, it might extract a sentence containing the word "Python" as a skill, but it won't know if the context was "I hate Python" versus "Expert in Python". (Though word matching mitigates this by just listing the skill).

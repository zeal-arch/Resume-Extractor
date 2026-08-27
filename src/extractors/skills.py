"""
src/extractors/skills.py
────────────────────────
Extracts technical skills from resume text by matching against a predefined
vocabulary. No LLM or external API is used.

Two matching strategies
───────────────────────
1. TECH_SKILLS (word-boundary safe):
   Standard alphanumeric/hyphenated skills (Python, Django, machine learning…)
   are matched with a `\\b` word-boundary regex. This avoids substring false
   positives (e.g. 'r' matching inside 'server').

2. SKILLS_SPECIAL_CHARS (custom boundary check):
   Skills containing non-word characters (+, #, .) such as C++, C#, ASP.NET
   break `\\b` matching. We use a direct substring search and verify that the
   character immediately before and after the match is not alphanumeric.
"""

import re

# Skills safe for \b word-boundary regex
TECH_SKILLS: set[str] = {
    # Languages
    "python", "java", "ruby", "javascript", "typescript", "go", "rust",
    "swift", "kotlin", "php", "sql", "html", "css", "r", "matlab", "scala",
    "perl", "bash", "shell", "powershell", "dart",

    # Frameworks / libraries
    "django", "flask", "fastapi", "spring", "spring boot", "react", "angular",
    "vue", "node.js", "express", "laravel", "hibernate", "flutter",
    "next.js", "nuxt.js",

    # Databases
    "mysql", "postgresql", "mongodb", "sqlite", "oracle", "redis",
    "cassandra", "elasticsearch", "neo4j", "dynamodb", "firebase",
    "sql server", "supabase",

    # Cloud / DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "jenkins",
    "gitlab ci", "github actions", "terraform", "ansible", "puppet", "chef",
    "linux", "unix", "cloudflare",

    # Data / ML
    "machine learning", "deep learning", "nlp", "computer vision",
    "data science", "data analysis", "artificial intelligence", "pandas",
    "numpy", "scikit-learn", "tensorflow", "keras", "pytorch", "matplotlib",
    "seaborn", "hadoop", "spark", "kafka", "tableau", "power bi",

    # Tools / Methods
    "git", "jira", "trello", "confluence", "agile", "scrum", "kanban",
    "bitbucket", "vite", "playwright", "puppeteer", "ffmpeg",

    # APIs / Architecture
    "rest api", "graphql", "grpc", "soap", "microservices", "websockets",
    "webassembly", "tailwind css", "zod",
}

# Skills that contain +, #, . or other non-word chars — need special boundary check
SKILLS_SPECIAL_CHARS: set[str] = {
    "C++", "C#", "C",           # C-family
    "ASP.NET", "ASP.NET Core",  # .NET stack
    ".NET", "VB.NET",
    "F#",
    "Objective-C",
    "R",                        # single-char; overlap with lang 'R'
}


def extract_skills(text: str) -> list[str]:
    """
    Return a sorted list of recognised skills found in the resume text.

    Parameters
    ----------
    text : str
        Plain text extracted from the resume.

    Returns
    -------
    list[str] — sorted, deduplicated skill names.
    """
    text_lower = text.lower()
    found: set[str] = set()

    # ── Strategy 1: word-boundary regex for standard skills ───────────────
    for skill in TECH_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.add(skill.title())

    # ── Strategy 2: custom boundary for special-char skills ───────────────
    for skill in SKILLS_SPECIAL_CHARS:
        skill_lower = skill.lower()
        idx = text_lower.find(skill_lower)
        if idx == -1:
            continue
        end = idx + len(skill_lower)
        before_ok = idx == 0 or not text_lower[idx - 1].isalnum()
        after_ok  = end >= len(text_lower) or not text_lower[end].isalnum()
        if before_ok and after_ok:
            found.add(skill)   # preserve original casing (e.g. 'C++', 'C#')

    return sorted(found)

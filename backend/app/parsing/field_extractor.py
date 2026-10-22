"""Regex + keyword-list based extraction of structured fields from raw resume text.

No LLM calls here on purpose -- this is the standard, cheap, deterministic approach
used in resume-screening portfolio projects: curated keyword lists plus regexes.
"""
import re

# A reasonably large curated list of common tech & business skills to look for.
# Lowercase; matching is done case-insensitively against resume text.
SKILLS_KEYWORDS: list[str] = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl", "dart",
    # Web / frontend
    "html", "css", "react", "reactjs", "angular", "vue", "vuejs", "svelte", "next.js",
    "nextjs", "redux", "jquery", "bootstrap", "tailwind", "sass", "webpack",
    # Backend / frameworks
    "django", "flask", "fastapi", "spring", "spring boot", "express", "express.js",
    "node.js", "nodejs", "asp.net", ".net", "rails", "laravel", "nestjs",
    # Databases
    "sql", "mysql", "postgresql", "postgres", "sqlite", "mongodb", "redis",
    "cassandra", "oracle", "dynamodb", "elasticsearch", "mariadb", "nosql",
    # Data / ML / AI
    "machine learning", "deep learning", "data science", "nlp",
    "natural language processing", "computer vision", "tensorflow", "pytorch",
    "keras", "scikit-learn", "sklearn", "pandas", "numpy", "matplotlib", "seaborn",
    "opencv", "data analysis", "data visualization", "statistics", "data mining",
    "artificial intelligence", "neural networks", "reinforcement learning",
    # Cloud / DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
    "jenkins", "ci/cd", "ansible", "linux", "unix", "bash", "shell scripting",
    "git", "github", "gitlab", "bitbucket", "devops", "nginx", "apache",
    "microservices", "serverless", "lambda", "cloudformation",
    # Mobile
    "android", "ios", "react native", "flutter", "xamarin",
    # Project management / business
    "agile", "scrum", "kanban", "jira", "project management", "product management",
    "business analysis", "stakeholder management", "risk management",
    "budgeting", "forecasting", "strategic planning",
    # Soft / general business
    "leadership", "communication", "teamwork", "problem solving",
    "critical thinking", "negotiation", "presentation", "time management",
    # Design
    "figma", "sketch", "adobe xd", "photoshop", "illustrator", "ui/ux", "ux design",
    "ui design", "graphic design",
    # Testing
    "selenium", "junit", "pytest", "unit testing", "test automation", "qa testing",
    # Other common tools
    "excel", "powerpoint", "tableau", "power bi", "sap", "salesforce", "crm",
    "rest api", "graphql", "api development", "microsoft office", "vba",
    "blockchain", "solidity", "cybersecurity", "penetration testing", "networking",
    "tcp/ip", "cryptography",
]

# Precompiled, word-boundary-aware regex per skill (built once at import time).
_SKILLS_PATTERN = {
    skill: re.compile(
        r"(?<![a-zA-Z0-9])" + re.escape(skill).replace(r"\ ", r"[\s\-]*") + r"(?![a-zA-Z0-9])",
        re.IGNORECASE,
    )
    for skill in SKILLS_KEYWORDS
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

PHONE_RE = re.compile(
    r"(\+?\d{1,3}[\s.\-]?)?(\(?\d{2,4}\)?[\s.\-]?)?\d{3,4}[\s.\-]?\d{3,4}(?:[\s.\-]?\d{2,4})?"
)

# A phone candidate must have at least this many digits to be considered valid,
# to avoid matching random short numbers.
MIN_PHONE_DIGITS = 7
MAX_PHONE_DIGITS = 15

DEGREE_KEYWORDS = [
    "ph.d", "phd", "doctorate", "master of", "m.sc", "msc", "m.s.", "mba",
    "bachelor of", "b.sc", "bsc", "b.s.", "b.tech", "btech", "m.tech", "mtech",
    "associate degree", "high school diploma", "diploma", "b.e.", "be ", "m.e.",
]

CERTIFICATION_KEYWORDS = [
    "aws certified", "azure certified", "google certified", "pmp", "scrum master",
    "csm", "cissp", "comptia", "ccna", "ccnp", "oracle certified", "six sigma",
    "itil", "cfa", "cpa", "certified", "certification",
]

ACTION_VERBS = [
    "led", "managed", "developed", "designed", "implemented", "built", "created",
    "improved", "increased", "reduced", "optimized", "launched", "coordinated",
    "spearheaded", "delivered", "achieved", "analyzed", "automated", "streamlined",
    "mentored", "architected", "deployed", "engineered",
]

EXPERIENCE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)?",
    re.IGNORECASE,
)

NAME_LINE_SKIP_KEYWORDS = [
    "resume", "curriculum vitae", "cv", "email", "phone", "address", "objective",
    "summary", "profile",
]


def extract_email(text: str) -> str | None:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    for match in PHONE_RE.finditer(text):
        candidate = match.group(0)
        digits = re.sub(r"\D", "", candidate)
        if MIN_PHONE_DIGITS <= len(digits) <= MAX_PHONE_DIGITS:
            return candidate.strip()
    return None


def extract_name(text: str) -> str | None:
    """Best-effort guess: first non-empty line that looks like a person's name
    (short, title-cased, no digits, not a known header keyword)."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines[:8]:
        lower = line.lower()
        if any(kw in lower for kw in NAME_LINE_SKIP_KEYWORDS):
            continue
        if EMAIL_RE.search(line):
            continue
        if any(ch.isdigit() for ch in line):
            continue
        words = line.split()
        if 1 <= len(words) <= 4 and all(w[0].isupper() or not w[0].isalpha() for w in words if w):
            return line
    return None


def extract_skills(text: str) -> list[str]:
    found = []
    for skill, pattern in _SKILLS_PATTERN.items():
        if pattern.search(text):
            found.append(skill)
    return sorted(set(found))


def extract_education(text: str) -> list[str]:
    found = []
    lower = text.lower()
    for kw in DEGREE_KEYWORDS:
        if kw in lower:
            # Try to capture the surrounding line for more context.
            for line in text.splitlines():
                if kw in line.lower():
                    found.append(line.strip())
                    break
            else:
                found.append(kw)
    # De-duplicate while preserving order.
    seen = set()
    result = []
    for item in found:
        if item.lower() not in seen:
            seen.add(item.lower())
            result.append(item)
    return result


def extract_certifications(text: str) -> list[str]:
    found = []
    lower = text.lower()
    for kw in CERTIFICATION_KEYWORDS:
        if kw in lower:
            for line in text.splitlines():
                if kw in line.lower():
                    found.append(line.strip())
                    break
    seen = set()
    result = []
    for item in found:
        if item.lower() not in seen:
            seen.add(item.lower())
            result.append(item)
    return result


def extract_experience_years(text: str) -> float:
    matches = EXPERIENCE_RE.findall(text)
    years = [float(m) for m in matches if m]
    if years:
        return max(years)
    return 0.0


def extract_all_fields(text: str) -> dict:
    """Run all extractors and return a dict ready to populate a Candidate row."""
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "certifications": extract_certifications(text),
        "experience_years": extract_experience_years(text),
    }

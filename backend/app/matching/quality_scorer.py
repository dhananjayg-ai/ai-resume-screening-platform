"""Heuristic resume quality scoring + actionable suggestions.

Checks: presence of contact info, quantified achievements, action verbs,
resume length, section completeness, and some basic formatting red flags.
"""
import re

from app.parsing.field_extractor import ACTION_VERBS

QUANTIFIED_RE = re.compile(r"\d+(\.\d+)?\s*(%|percent|\$|years?|yrs?|users?|clients?|projects?|million|thousand|k\b)", re.IGNORECASE)

SECTION_KEYWORDS = {
    "experience": ["experience", "work history", "employment"],
    "education": ["education", "academic"],
    "skills": ["skills", "technical skills", "competencies"],
    "summary": ["summary", "objective", "profile"],
}

MIN_WORD_COUNT = 150
MAX_WORD_COUNT = 1200


def score_resume_quality(
    raw_text: str,
    email: str | None,
    phone: str | None,
    skills: list[str],
) -> tuple[float, list[str]]:
    """Return (quality_score 0-100, list of suggestion strings)."""
    suggestions: list[str] = []
    points = 0
    max_points = 0
    text_lower = (raw_text or "").lower()
    word_count = len(raw_text.split()) if raw_text else 0

    # 1. Contact info presence
    max_points += 20
    if email and phone:
        points += 20
    elif email or phone:
        points += 10
        suggestions.append(
            "Add both an email address and a phone number so recruiters can reach you."
        )
    else:
        suggestions.append(
            "No contact information detected. Add your email and phone number near the top of the resume."
        )

    # 2. Quantified achievements
    max_points += 20
    quantified_matches = len(QUANTIFIED_RE.findall(raw_text or ""))
    if quantified_matches >= 3:
        points += 20
    elif quantified_matches >= 1:
        points += 10
        suggestions.append(
            "Add more quantified achievements (e.g. 'increased sales by 20%', 'managed a team of 5')."
        )
    else:
        suggestions.append(
            "Quantify your achievements with numbers, percentages, or scale (e.g. '$2M in revenue', '30% faster')."
        )

    # 3. Action verbs
    max_points += 15
    verb_hits = sum(1 for verb in ACTION_VERBS if verb in text_lower)
    if verb_hits >= 5:
        points += 15
    elif verb_hits >= 2:
        points += 8
        suggestions.append(
            "Use more strong action verbs (e.g. 'led', 'built', 'optimized') to start your bullet points."
        )
    else:
        suggestions.append(
            "Start bullet points with strong action verbs like 'led', 'built', 'designed', or 'improved'."
        )

    # 4. Length
    max_points += 15
    if MIN_WORD_COUNT <= word_count <= MAX_WORD_COUNT:
        points += 15
    elif word_count < MIN_WORD_COUNT:
        points += 5
        suggestions.append(
            "Your resume looks quite short. Add more detail about your experience, projects, and accomplishments."
        )
    else:
        points += 8
        suggestions.append(
            "Your resume is quite long. Consider trimming it to focus on the most relevant and recent experience."
        )

    # 5. Section completeness
    max_points += 20
    sections_found = 0
    for section, keywords in SECTION_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            sections_found += 1
        else:
            suggestions.append(f"Consider adding a clear '{section.title()}' section.")
    points += round(20 * sections_found / len(SECTION_KEYWORDS))

    # 6. Skills presence
    max_points += 10
    if len(skills) >= 5:
        points += 10
    elif len(skills) >= 1:
        points += 5
        suggestions.append("List more of your relevant technical and professional skills.")
    else:
        suggestions.append("No recognizable skills found. Add a dedicated skills section.")

    # 7. Formatting red flags
    if raw_text and len(raw_text.strip()) < 50:
        suggestions.append(
            "Very little text could be extracted. If this is a scanned document, ensure OCR quality is good, "
            "or provide a text-based PDF/DOCX."
        )
    if raw_text and raw_text.count("\t") > 50:
        suggestions.append("Avoid excessive tab characters/complex tables, which can confuse automated parsers.")

    score = round(100 * points / max_points, 2) if max_points else 0.0
    score = max(0.0, min(100.0, score))

    if not suggestions:
        suggestions.append("Great resume! No major issues detected.")

    return score, suggestions

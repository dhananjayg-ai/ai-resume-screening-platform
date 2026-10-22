"""Skill-gap recommendations: compare candidate skills vs job required skills
and map missing skills to curated learning resources.
"""

# Curated learning resources per skill area. Keys are lowercase skill names
# matching (a subset of) the SKILLS_KEYWORDS list in field_extractor.py.
# At least 15-20 entries covering common tech/business skills.
LEARNING_RESOURCES: dict[str, list[dict[str, str]]] = {
    "python": [
        {"name": "Python Official Tutorial", "url": "https://docs.python.org/3/tutorial/"},
        {"name": "Automate the Boring Stuff with Python", "url": "https://automatetheboringstuff.com/"},
    ],
    "java": [
        {"name": "Oracle Java Tutorials", "url": "https://docs.oracle.com/javase/tutorial/"},
    ],
    "javascript": [
        {"name": "MDN JavaScript Guide", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"},
    ],
    "sql": [
        {"name": "Mode SQL Tutorial", "url": "https://mode.com/sql-tutorial/"},
        {"name": "W3Schools SQL", "url": "https://www.w3schools.com/sql/"},
    ],
    "aws": [
        {"name": "AWS Skill Builder (Free Training)", "url": "https://skillbuilder.aws/"},
        {"name": "AWS Certified Cloud Practitioner Guide", "url": "https://aws.amazon.com/certification/certified-cloud-practitioner/"},
    ],
    "azure": [
        {"name": "Microsoft Learn: Azure Fundamentals", "url": "https://learn.microsoft.com/en-us/training/azure/"},
    ],
    "gcp": [
        {"name": "Google Cloud Skills Boost", "url": "https://www.cloudskillsboost.google/"},
    ],
    "docker": [
        {"name": "Docker Official Getting Started", "url": "https://docs.docker.com/get-started/"},
    ],
    "kubernetes": [
        {"name": "Kubernetes Official Docs", "url": "https://kubernetes.io/docs/tutorials/"},
    ],
    "react": [
        {"name": "React Official Docs", "url": "https://react.dev/learn"},
    ],
    "machine learning": [
        {"name": "Andrew Ng's Machine Learning (Coursera)", "url": "https://www.coursera.org/learn/machine-learning"},
        {"name": "scikit-learn User Guide", "url": "https://scikit-learn.org/stable/user_guide.html"},
    ],
    "deep learning": [
        {"name": "DeepLearning.AI Specialization", "url": "https://www.coursera.org/specializations/deep-learning"},
    ],
    "data science": [
        {"name": "Kaggle Learn", "url": "https://www.kaggle.com/learn"},
    ],
    "data analysis": [
        {"name": "Kaggle Learn: Pandas", "url": "https://www.kaggle.com/learn/pandas"},
    ],
    "git": [
        {"name": "Pro Git Book", "url": "https://git-scm.com/book/en/v2"},
    ],
    "linux": [
        {"name": "Linux Journey", "url": "https://linuxjourney.com/"},
    ],
    "agile": [
        {"name": "Atlassian Agile Coach", "url": "https://www.atlassian.com/agile"},
    ],
    "scrum": [
        {"name": "Scrum.org Learning Series", "url": "https://www.scrum.org/resources"},
    ],
    "project management": [
        {"name": "Google Project Management Certificate", "url": "https://www.coursera.org/professional-certificates/google-project-management"},
    ],
    "excel": [
        {"name": "Microsoft Excel Training", "url": "https://support.microsoft.com/en-us/excel"},
    ],
    "tableau": [
        {"name": "Tableau Free Training Videos", "url": "https://www.tableau.com/learn/training"},
    ],
    "power bi": [
        {"name": "Microsoft Learn: Power BI", "url": "https://learn.microsoft.com/en-us/power-bi/"},
    ],
    "django": [
        {"name": "Django Official Tutorial", "url": "https://docs.djangoproject.com/en/stable/intro/tutorial01/"},
    ],
    "fastapi": [
        {"name": "FastAPI Official Tutorial", "url": "https://fastapi.tiangolo.com/tutorial/"},
    ],
    "node.js": [
        {"name": "Node.js Official Guides", "url": "https://nodejs.org/en/docs/guides"},
    ],
    "communication": [
        {"name": "Coursera: Improving Communication Skills", "url": "https://www.coursera.org/learn/wharton-communication-skills"},
    ],
    "leadership": [
        {"name": "Coursera: Leadership Development", "url": "https://www.coursera.org/browse/business/leadership-and-management"},
    ],
    "cybersecurity": [
        {"name": "Cybrary Free Cybersecurity Courses", "url": "https://www.cybrary.it/"},
    ],
    "salesforce": [
        {"name": "Salesforce Trailhead", "url": "https://trailhead.salesforce.com/"},
    ],
}

# Fallback generic resource for skills without a curated entry.
_GENERIC_RESOURCE_TEMPLATE = {
    "name": "Search courses on this topic (Coursera)",
    "url": "https://www.coursera.org/search?query={query}",
}


def get_learning_resources_for_skill(skill: str) -> list[dict[str, str]]:
    key = skill.lower().strip()
    if key in LEARNING_RESOURCES:
        return LEARNING_RESOURCES[key]
    query = key.replace(" ", "+")
    return [{"name": _GENERIC_RESOURCE_TEMPLATE["name"], "url": _GENERIC_RESOURCE_TEMPLATE["url"].format(query=query)}]


def build_skill_gap_recommendations(missing_skills: list[str]) -> dict[str, list[dict[str, str]]]:
    """Map each missing skill to a list of learning resources."""
    return {skill: get_learning_resources_for_skill(skill) for skill in missing_skills}

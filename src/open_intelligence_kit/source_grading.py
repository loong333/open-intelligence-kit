from __future__ import annotations

ALLOWED_GRADES = {"S", "A", "B", "C", "D", "unknown"}

GRADE_DESCRIPTIONS = {
    "S": "Official docs, official announcements, laws, standards, code releases.",
    "A": "Company sites, maintainer blogs, authoritative reports, first-party interviews.",
    "B": "Mainstream media, credible blogs, community discussions.",
    "C": "Social samples, comments, forums, screenshots with context; signal only.",
    "D": "Marketing reposts, unsourced screenshots, one-off rumors; lead only.",
    "unknown": "Not graded yet.",
}


def normalize_grade(grade: str) -> str:
    grade = (grade or "unknown").strip()
    if grade not in ALLOWED_GRADES:
        raise ValueError(f"source grade must be one of {sorted(ALLOWED_GRADES)}")
    return grade

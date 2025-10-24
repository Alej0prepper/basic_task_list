import re
from typing import List

# Emails y URLs están bien tal cual
EMAIL_REGEX = r"(?i)(?<![\w.])(?:[a-z0-9._%+-]+)@(?:[a-z0-9.-]+\.[a-z]{2,})"
URL_REGEX = r"(?i)\bhttps?://[\w\-._~:/?#[\]@!$&'()*+,;=%]+\b"

# Evitar look-behind variable-width:
# (?<!\S) significa "no hay un no-espacio antes" => inicio de línea o espacio
MENTION_REGEX = r"(?<!\S)@[A-Za-z0-9_-]+"
HASHTAG_REGEX = r"(?<!\S)#[A-Za-z0-9_-]+"

def extract_tags(text: str) -> List[str]:
    """Devuelve una lista única y ordenada de tags encontrados en 'text'."""
    found = set()

    for m in re.findall(EMAIL_REGEX, text):
        found.add(m)

    for m in re.findall(URL_REGEX, text):
        found.add(m)

    for m in re.findall(MENTION_REGEX, text):
        found.add(m)

    for m in re.findall(HASHTAG_REGEX, text):
        found.add(m)

    return sorted(found)

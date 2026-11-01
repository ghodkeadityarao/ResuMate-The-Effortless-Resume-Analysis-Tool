"""Split resume text into lines, achievement statements and sections."""
import re

from .wordlists import HEADINGS

BULLET = "•"
MARKERS = r"[•\-–—*>]"
_HEADING_LOOKUP = {phrase: kind for kind, phrases in HEADINGS.items() for phrase in phrases}
_HEADING_START = re.compile(
    r"^\W*(" + "|".join(sorted((re.escape(p) for p in _HEADING_LOOKUP), key=len, reverse=True)) + r")\b[ \t]*(?::|\*|$)",
    re.IGNORECASE)


def words(text):
    return re.findall(r"[A-Za-z][A-Za-z'+#.-]*|\d+(?:\.\d+)?", text)


def split_sections(text):
    """{kind: text} for the headings found (summary, education, experience, projects, skills, achievements)."""
    sections, current, buffer = {}, None, []
    for line in text.split("\n"):
        stripped = line.strip()
        m = _HEADING_START.match(stripped)
        if m:
            if current:
                sections[current] = sections.get(current, "") + "\n".join(buffer) + "\n"
            current, buffer = _HEADING_LOOKUP[m.group(1).lower()], [stripped[m.end():]]
        else:
            buffer.append(line)
    if current:
        sections[current] = sections.get(current, "") + "\n".join(buffer)
    return {k: v.strip() for k, v in sections.items() if v.strip()}


def statements(text):
    """The achievement lines of a resume: bullet lines when there are enough, otherwise sentence-like lines."""
    bullets = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith(BULLET) or re.match(MARKERS + r"\s+\S", line):
            body = re.sub("^" + MARKERS + r"\s*", "", line).strip()
            if len(body.split()) >= 3:
                bullets.append(body)
    if len(bullets) >= 4:
        return bullets
    return [ln.strip() for ln in text.split("\n") if len(ln.split()) >= 7 and not _HEADING_START.match(ln.strip())]


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text) if len(s.split()) >= 3]

"""Skill vocabulary and skill extraction.

The vocabulary (data/skills.txt) comes from the two skill lists the project already had, cleaned by
scripts/build_skills.py. A skill is found when its words appear in the text as an exact phrase.
"""
import re
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
TOKEN = re.compile(r"\.?[A-Za-z0-9][A-Za-z0-9+#./&-]*")
MAX_WORDS = 4


def normalise(token):
    return token.lower().rstrip(".-/&")


@lru_cache(maxsize=1)
def vocabulary():
    """{lower-case phrase: display name}."""
    out = {}
    for line in (DATA / "skills.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.setdefault(" ".join(normalise(t) for t in TOKEN.findall(line)), line.strip())
    out.pop("", None)
    return out


def phrases(text, longest=MAX_WORDS):
    """Every run of up to `longest` consecutive words, lower-cased, with how often it occurs."""
    tokens = [normalise(t) for t in TOKEN.findall(text)]
    counts = {}
    for i in range(len(tokens)):
        for n in range(1, longest + 1):
            if i + n <= len(tokens):
                gram = " ".join(tokens[i:i + n])
                counts[gram] = counts.get(gram, 0) + 1
    return counts


def extract_skills(text):
    """[(display name, count)] of vocabulary skills in the text, most mentioned first."""
    vocab, found = vocabulary(), []
    for gram, count in phrases(text).items():
        if gram in vocab:
            found.append((vocab[gram], count))
    found.sort(key=lambda kv: (-kv[1], kv[0].lower()))
    return found

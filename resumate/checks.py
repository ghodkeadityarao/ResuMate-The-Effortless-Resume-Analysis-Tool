"""The scored checks. Each takes a Document and returns a Finding with its points, the evidence and a tip.

The points of all checks add up to 100, split over four categories:
    Impact 30, Brevity 20, Style 25, Sections 25.
Points are earned in proportion (a resume that is half-way to a target earns about half the points),
not in steps, so a small improvement always moves the score.
"""
import re
import statistics
from dataclasses import dataclass, field
from functools import lru_cache

from . import skills
from .textutils import sentences, split_sections, statements
from .wordlists import CLICHES, IRREGULAR_PARTICIPLES, STRONG_VERBS, WEAK_PHRASES

CATEGORIES = {"Impact": 30, "Brevity": 20, "Style": 25, "Sections": 25}


@dataclass
class Finding:
    key: str
    category: str
    title: str
    max_points: float
    score: float
    summary: str
    evidence: list = field(default_factory=list)
    tip: str = ""

    @property
    def lost(self):
        return self.max_points - self.score


def clamp(x, low=0.0, high=1.0):
    return max(low, min(high, x))


def ramp(x, zero_at, full_at):
    """0 at `zero_at`, 1 at `full_at`, straight line between (works in either direction)."""
    return clamp((x - zero_at) / (full_at - zero_at))


def make(key, category, title, max_points, fraction, summary, evidence=(), tip=""):
    return Finding(key, category, title, max_points, round(max_points * clamp(fraction), 1), summary, list(evidence)[:8], tip)


# --- Impact (30) ---------------------------------------------------------------------------

YEAR = re.compile(r"\b(?:19|20)\d{2}\b")
METRIC = re.compile(
    r"\d+(?:\.\d+)?\s?%|[$₹£€]\s?\d|\b\d+(?:\.\d+)?\s?(?:x|k|m|mn|bn|lakhs?|crores?|million|billion|thousand)\b"
    r"|\b\d{1,3}(?:,\d{3})+\b|\b\d{2,}\+?\s+(?:users|customers|clients|students|members|employees|projects|requests|"
    r"records|transactions|engineers|developers|stores|accounts|reports|models|tests|applications|apps|pages|"
    r"visitors|downloads|orders|tickets|leads|people|teams|countries|cities|hours|days|weeks|months)\b"
    r"|\b\d+(?:\.\d+)?\s?(?:ms|seconds|minutes|hrs|hours)\b", re.IGNORECASE)


def has_metric(statement):
    without_years = YEAR.sub(" ", statement)
    return bool(METRIC.search(without_years)) or bool(re.search(r"(?<![\w.])\d{2,}(?![\w.])", without_years))


def quantified_results(doc):
    lines = statements(doc.text)
    if not lines:
        return make("quantified", "Impact", "Numbers that show results", 10, 0, "No achievement lines were found.",
                    tip="Write each achievement as a line that starts with a verb and says what changed, with a number.")
    with_numbers = [s for s in lines if has_metric(s)]
    ratio = len(with_numbers) / len(lines)
    missing = [s for s in lines if not has_metric(s)]
    return make("quantified", "Impact", "Numbers that show results", 10, ramp(ratio, 0, 0.4),
                f"{len(with_numbers)} of {len(lines)} achievement lines contain a result you can measure ({ratio:.0%}). "
                f"Aim for at least 40%.", [f"No number: {s[:140]}" for s in missing],
                "Add a figure to your lines: how much, how many, how fast, how often, or by what percentage.")


def strong_verbs(doc):
    lines = statements(doc.text)
    if not lines:
        return make("verbs", "Impact", "Strong opening verbs", 8, 0, "No achievement lines were found.")
    strong, weak_open = 0, []
    for s in lines:
        first = re.sub(r"[^a-z]", "", s.split()[0].lower())
        if first in STRONG_VERBS:
            strong += 1
        else:
            weak_open.append(s)
    ratio = strong / len(lines)
    return make("verbs", "Impact", "Strong opening verbs", 8, ramp(ratio, 0, 0.7),
                f"{strong} of {len(lines)} achievement lines open with a strong action verb ({ratio:.0%}). Aim for at least 70%.",
                [f"Opens with '{s.split()[0]}': {s[:120]}" for s in weak_open],
                "Start each line with what you did, in the past tense: Built, Reduced, Led, Automated.")


def weak_phrases(doc):
    text = doc.text.lower()
    hits = [(p, len(re.findall(r"\b" + re.escape(p) + r"\b", text))) for p in WEAK_PHRASES]
    hits = [(p, n) for p, n in hits if n]
    total = sum(n for _, n in hits)
    return make("weak", "Impact", "Vague phrases", 6, 1 - total / 4,
                "No vague phrases found." if not total else f"{total} vague phrase(s) found.",
                [f"'{p}' appears {n}x" for p, n in hits],
                "Replace 'responsible for' or 'worked on' with the result you produced.")


def repetition(doc):
    seen, repeated = {}, []
    for s in sentences(doc.text):
        key = re.sub(r"\W+", " ", s.lower()).strip()
        seen[key] = seen.get(key, 0) + 1
    repeated = [k for k, n in seen.items() if n > 1]
    starts = {}
    for s in statements(doc.text):
        first = re.sub(r"[^a-z]", "", s.split()[0].lower())
        starts[first] = starts.get(first, 0) + 1
    overused = [(v, n) for v, n in starts.items() if n >= 4 and v in STRONG_VERBS]
    penalty = len(repeated) + sum(n - 3 for _, n in overused) * 0.5
    evidence = [f"Sentence repeated: {k[:120]}" for k in repeated] + [f"'{v}' starts {n} lines" for v, n in overused]
    return make("repetition", "Impact", "Repetition", 6, 1 - penalty / 4,
                "No repeated sentences or overused opening verbs." if not evidence else f"{len(evidence)} repetition(s) found.",
                evidence, "Say each thing once and vary your opening verbs.")


# --- Brevity (20) --------------------------------------------------------------------------

def length(doc):
    n = len(doc.text.split())
    fraction = 1.0 if 400 <= n <= 700 else (ramp(n, 150, 400) if n < 400 else ramp(n, 1100, 700))
    advice = "A good resume is roughly 400 to 700 words."
    return make("length", "Brevity", "Length", 8, fraction, f"{n} words. {advice}", [],
                "Add detail about your strongest work." if n < 400 else "Cut older or less relevant detail." if n > 700 else "")


def pages(doc):
    p = doc.pages
    fraction = 1.0 if p <= 2 else (0.5 if p == 3 else 0.0)
    return make("pages", "Brevity", "Pages", 4, fraction, f"{p} page(s). One or two pages is the norm.",
                tip="Keep to two pages; one page if you have under ten years of experience.")


def line_length(doc):
    lines = statements(doc.text)
    if not lines:
        return make("line_length", "Brevity", "Achievement line length", 4, 0, "No achievement lines were found.")
    median = statistics.median(len(s.split()) for s in lines)
    too_long = [s for s in lines if len(s.split()) > 35]
    fraction = 1.0 if 8 <= median <= 28 else (ramp(median, 3, 8) if median < 8 else ramp(median, 45, 28))
    return make("line_length", "Brevity", "Achievement line length", 4, fraction,
                f"The typical achievement line is {median:.0f} words. 8 to 28 reads best.",
                [f"{len(s.split())} words: {s[:110]}..." for s in too_long], "Split long lines in two; expand very short ones.")


def line_count(doc):
    n = len(statements(doc.text))
    return make("line_count", "Brevity", "Number of achievement lines", 4, ramp(n, 0, 8),
                f"{n} achievement lines. At least 8 gives enough to judge your work.", tip="Add bullets for your main projects and jobs.")


# --- Style (25) ----------------------------------------------------------------------------

BE = r"(?:is|are|was|were|be|been|being)"
PASSIVE = re.compile(r"\b" + BE + r"\s+(?:\w+ly\s+)?(?:\w{3,}ed|" + IRREGULAR_PARTICIPLES + r")\b(?!\s+(?:to|of)\b)", re.IGNORECASE)
NOT_PASSIVE = re.compile(r"\b(?:is|are|was|were|be|been|being)\s+(?:interested|motivated|experienced|skilled|qualified|"
                         r"detailed|related|based|excited|pleased|involved|determined|dedicated|supposed|used\sto)\b", re.IGNORECASE)


def passive_voice(doc):
    hits = [s for s in sentences(doc.text) if PASSIVE.search(s) and not NOT_PASSIVE.search(s)]
    return make("passive", "Style", "Passive voice", 5, 1 - len(hits) / 5,
                "No passive sentences found." if not hits else f"{len(hits)} sentence(s) are in the passive voice.",
                [s[:140] for s in hits], "Say who did it: 'Built the API' instead of 'The API was built'.")


def pronouns(doc):
    found = re.findall(r"\b(?:I|me|my|mine|myself)\b", doc.text)
    return make("pronouns", "Style", "First-person words", 4, 1 - len(found) / 4,
                "No 'I', 'me' or 'my' found." if not found else f"{len(found)} first-person word(s): {', '.join(sorted(set(found)))}.",
                tip="Resumes leave out 'I' and 'my'; start with the verb.")


def cliches(doc):
    text = doc.text.lower()
    hits = [p for p in CLICHES if re.search(r"\b" + re.escape(p) + r"\b", text)]
    return make("cliches", "Style", "Stock phrases", 6, 1 - len(hits) / 4,
                "No stock phrases found." if not hits else f"{len(hits)} stock phrase(s) found.", [f"'{p}'" for p in hits],
                "Show the quality with an example instead of naming it.")


@lru_cache(maxsize=1)
def _speller():
    from spellchecker import SpellChecker
    known = {t for phrase in skills.vocabulary() for t in phrase.split()}
    return SpellChecker(), known


def spelling(doc):
    checker, known = _speller()
    text = re.sub(r"https?://\S+|\S+@\S+|\S+\.(?:com|in|io|org|net|dev)\S*", " ", doc.text)
    candidates = re.findall(r"\b[a-z]{3,}\b", text)
    wrong = [w for w in checker.unknown(candidates) if w not in known]
    rate = len(wrong) / max(len(candidates), 1)
    shown = sorted(set(wrong))
    return make("spelling", "Style", "Spelling", 6, ramp(rate, 0.06, 0.01),
                f"{len(shown)} possible misspelling(s) in {len(candidates)} lower-case words ({rate:.1%}).",
                [f"'{w}' (maybe '{checker.correction(w)}')" for w in shown[:8]], "Check these words; proper names and tools may be false alarms.")


DATE_FORMATS = [
    ("Mon YYYY", re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?,?\s+(?:19|20)\d{2}\b")),
    ("MM/YYYY", re.compile(r"\b(?:0?[1-9]|1[0-2])[/-](?:19|20)\d{2}\b")),
    ("YYYY", re.compile(r"(?<![/\w-])(?:19|20)\d{2}(?![/\w-])")),
]


def dates(doc):
    counts = {}
    remaining = doc.text
    for label, pattern in DATE_FORMATS:
        found = pattern.findall(remaining)
        if found:
            counts[label] = len(found)
            remaining = pattern.sub(" ", remaining)
    total = sum(counts.values())
    if total < 2:
        return make("dates", "Style", "Dates", 4, 0, "Fewer than two dates found.", tip="Give start and end dates for jobs, projects and education.")
    detail = ", ".join(f"{k}: {v}" for k, v in counts.items())
    mixed = "Mon YYYY" in counts and "MM/YYYY" in counts            # a bare year next to month dates is normal
    return make("dates", "Style", "Dates", 4, 0.5 if mixed else 1.0,
                f"{total} dates found ({detail}).", ["Months are written in more than one style."] if mixed else [],
                "Write every date in one style, for example 'Jun 2023'.")


# --- Sections (25) -------------------------------------------------------------------------

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}|[6-9]\d{4}[\s-]?\d{5})(?!\d)")
LINK = re.compile(r"(?:https?://|www\.)\S+|(?:linkedin\.com|github\.com|gitlab\.com|behance\.net|kaggle\.com)/\S*", re.IGNORECASE)


def contact(doc):
    got = {"email": bool(EMAIL.search(doc.text)), "phone": bool(PHONE.search(doc.text)), "profile link": bool(LINK.search(doc.text))}
    points = (3 if got["email"] else 0) + (2 if got["phone"] else 0) + (3 if got["profile link"] else 0)
    missing = [k for k, ok in got.items() if not ok]
    return make("contact", "Sections", "Contact details", 8, points / 8,
                "Email, phone and a profile link are all there." if not missing else f"Missing: {', '.join(missing)}.", [],
                "Put your email, phone number and a LinkedIn or GitHub link at the top." if missing else "")


def _section(doc, key, title, points, tip, kinds=None):
    found = split_sections(doc.text)
    kinds = kinds or [key]
    ok = any(k in found for k in kinds)
    return make(key, "Sections", title, points, 1.0 if ok else 0,
                f"The {title.lower()} section was found." if ok else f"No {title.lower()} section was found.", [], "" if ok else tip)


def education(doc):
    return _section(doc, "education", "Education", 4, "Add an Education section with your degree, college and years.")


def experience(doc):
    return _section(doc, "experience", "Experience or projects", 6,
                    "Add an Experience or Projects section; recruiters read it first.", ["experience", "projects"])


def skills_section(doc):
    return _section(doc, "skills", "Skills", 4, "Add a Skills section that lists your tools and technologies.")


def summary(doc):
    return _section(doc, "summary", "Summary", 3, "Add two or three lines at the top saying who you are and what you aim for.")


CHECKS = [quantified_results, strong_verbs, weak_phrases, repetition, length, pages, line_length, line_count,
          passive_voice, pronouns, cliches, spelling, dates, contact, education, experience, skills_section, summary]

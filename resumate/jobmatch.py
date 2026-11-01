"""Compare a resume with a job post: which of the post's skills and keywords the resume covers.

Skills come from the skill vocabulary. Keywords are the words and word pairs of the post that carry the
most weight (TF-IDF, with the weights learnt from the resume dataset so everyday resume words count
for little). The match is a weighted share of what the post asks for that the resume mentions (a word pair counts when
both of its words appear).
"""
import re
from functools import lru_cache

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

from . import skills
from .roles import load_unique, tidy

BOILERPLATE = set("""
candidate candidates looking role position join company opportunity apply applicant ability strong excellent required
preferred responsibilities responsibility qualifications qualification experience years year work working team teams
including include includes etc must plus bonus benefits salary location equal employer description requirements
requirement skills skill knowledge good great able need needs new use using related relevant based will within across
""".split())
TOP_KEYWORDS = 25
SKILL_SHARE = 0.6                  # weight of skill coverage in the overall match when the post names skills
MIN_WORDS = 15


@lru_cache(maxsize=1)
def _vectorizer():
    texts, _, _ = load_unique()
    return TfidfVectorizer(sublinear_tf=True, stop_words="english", ngram_range=(1, 2), min_df=1).fit(texts)


def stem(term):
    """Fold simple plurals so 'apis' matches 'api'."""
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in term.split())


def keywords(job_text, n=TOP_KEYWORDS):
    """[(keyword, weight)] for the job post, heaviest first."""
    vec = _vectorizer()
    segments = [tidy(s) for s in re.split(r"[,;:()\n/\u2022]+|\.\s", job_text) if s.strip()]   # word pairs never cross punctuation
    rows = vec.transform(segments).sum(axis=0).A1
    names = vec.get_feature_names_out()
    scored = []
    for idx in rows.nonzero()[0]:
        term, weight = names[idx], rows[idx]
        if any(w in BOILERPLATE or w in ENGLISH_STOP_WORDS or len(w) < 2 for w in term.split()):
            continue
        scored.append((term, float(weight)))
    scored.sort(key=lambda kv: -kv[1])
    chosen = []
    for term, weight in scored:                       # skip a word when a listed pair already contains it
        if not any(term != other and term in other.split() for other, _ in chosen):
            chosen.append((term, weight))
        if len(chosen) == n:
            break
    return chosen


def _resume_terms(text):
    return {stem(w) for w in tidy(text).split()} | {stem(p) for p in skills.phrases(text)}


def _covered(term, terms):
    """A word is covered when the resume has it; a word pair when the resume has both words."""
    return stem(term) in terms or all(stem(w) in terms for w in term.split())


def match(resume_text, job_text):
    if len(job_text.split()) < MIN_WORDS:
        raise ValueError(f"Paste the full job description (at least {MIN_WORDS} words).")
    terms = _resume_terms(resume_text)
    job_skills = [name for name, _ in skills.extract_skills(job_text)]
    have = [s for s in job_skills if _covered(s.lower(), terms)]
    kws = keywords(job_text)
    kw_have = [(k, w) for k, w in kws if _covered(k, terms)]
    keyword_share = sum(w for _, w in kw_have) / sum(w for _, w in kws) if kws else 0.0
    skill_share = len(have) / len(job_skills) if job_skills else None
    overall = keyword_share if skill_share is None else SKILL_SHARE * skill_share + (1 - SKILL_SHARE) * keyword_share
    return {"match_percent": round(100 * overall), "skills_in_post": job_skills, "skills_found": have,
            "skills_missing": [s for s in job_skills if s not in have],
            "keywords_found": [k for k, _ in kw_have], "keywords_missing": [k for k, _ in kws if k not in {x for x, _ in kw_have}],
            "skill_share": None if skill_share is None else round(100 * skill_share), "keyword_share": round(100 * keyword_share)}

import re

import pytest

import samples
from resumate.checks import CATEGORIES, CHECKS
from resumate.extract import read_document
from resumate.scoring import analyze


def score(text):
    return analyze(read_document("r.txt", text.encode()))


def test_category_points_add_up_to_100_and_every_check_is_in_a_category():
    report = score(samples.GOOD)
    assert sum(CATEGORIES.values()) == 100
    assert sum(f.max_points for f in report.findings) == 100
    for name, points in CATEGORIES.items():
        assert sum(f.max_points for f in report.findings if f.category == name) == points
    assert len(report.findings) == len(CHECKS)


def test_a_good_resume_scores_high_and_never_above_100():
    report = score(samples.GOOD)
    assert 85 <= report.total <= 100
    assert all(0 <= f.score <= f.max_points for f in report.findings)


def test_the_same_resume_scores_the_same_in_every_format():
    totals = {kind: analyze(read_document("r", fn())).total
              for kind, fn in [("txt", samples.text_bytes), ("docx", samples.docx_bytes), ("pdf", samples.pdf_bytes)]}
    assert len(set(totals.values())) == 1


DAMAGE = {
    "no contact details": lambda t: re.sub(r"asha\.verma@example\.com \| \+91 98765 43210 \| linkedin\.com/in/ashaverma \| github\.com/ashaverma", "", t),
    "no numbers": lambda t: re.sub(r"\d[\d,.]*%?", "", t),
    "no sections": lambda t: re.sub(r"^(SUMMARY|EXPERIENCE|PROJECTS|EDUCATION|SKILLS|ACHIEVEMENTS)$", "", t, flags=re.M),
    "vague wording": lambda t: t.replace("Built", "Responsible for building").replace("Led", "Worked on leading").replace("Reduced", "Helped with reducing"),
    "stock phrases": lambda t: t + "\nHard-working team player and self-starter, highly motivated and passionate. References available upon request.",
    "first person": lambda t: t.replace("• Built", "• I built my").replace("• Led", "• I led my").replace("• Won", "• I won my"),
    "much too short": lambda t: "\n".join(t.split("\n")[:12]),
}


@pytest.mark.parametrize("name", list(DAMAGE))
def test_damaging_a_resume_lowers_its_score(name):
    assert score(DAMAGE[name](samples.GOOD)).total < score(samples.GOOD).total - 3


def test_adding_a_number_to_a_bullet_never_lowers_the_score():
    base = "Built a service for the whole team to use daily."
    low = score(samples.GOOD.replace("Built a REST API in Flask serving 120,000 requests a day, cutting average response time by 38%.", base))
    high = score(samples.GOOD)
    assert high.total >= low.total


def test_biggest_gains_are_the_checks_that_lost_most():
    report = score(DAMAGE["no sections"](samples.GOOD))
    gains = report.biggest_gains()
    assert gains and gains[0].lost >= gains[-1].lost

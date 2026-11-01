"""Run every check and total the score."""
from dataclasses import dataclass

from . import skills
from .checks import CATEGORIES, CHECKS
from .textutils import split_sections


@dataclass
class Report:
    total: float
    categories: dict            # name -> (score, max)
    findings: list
    words: int
    pages: int
    sections: list              # kinds of section found
    skills: list                # [(skill, count)]

    def biggest_gains(self, n=5):
        return sorted((f for f in self.findings if f.lost >= 0.5), key=lambda f: -f.lost)[:n]


def analyze(doc):
    findings = [check(doc) for check in CHECKS]
    categories = {name: (round(sum(f.score for f in findings if f.category == name), 1), points)
                  for name, points in CATEGORIES.items()}
    return Report(round(sum(f.score for f in findings), 1), categories, findings, len(doc.text.split()), doc.pages,
                  sorted(split_sections(doc.text)), skills.extract_skills(doc.text))

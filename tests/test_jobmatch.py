import pytest

import samples
from resumate import jobmatch, skills

PYTHON_JOB = """We need a backend engineer with strong Python, Flask and Django experience. You will design REST APIs,
write tests with pytest, work with PostgreSQL and MySQL, and deploy services on AWS using Docker."""
NURSING_JOB = """We are hiring a registered nurse for our hospital ward. You will assess patients, administer medication,
record vital signs, support doctors during rounds and keep clear patient records in line with infection control policy."""


def test_a_matching_job_scores_higher_than_an_unrelated_one():
    good = jobmatch.match(samples.GOOD, PYTHON_JOB)
    bad = jobmatch.match(samples.GOOD, NURSING_JOB)
    assert good["match_percent"] >= 60 and bad["match_percent"] <= 20 and good["match_percent"] > bad["match_percent"] + 40


def test_skills_are_split_into_found_and_missing():
    job = PYTHON_JOB + " Experience with Kubernetes and Terraform is required."
    result = jobmatch.match(samples.GOOD, job)
    assert {"Python", "Flask", "Docker"} <= set(result["skills_found"])
    assert {"Kubernetes", "Terraform"} <= set(result["skills_missing"])


def test_adding_the_missing_skills_to_the_resume_raises_the_match():
    job = PYTHON_JOB + " Experience with Kubernetes and Terraform is required."
    before = jobmatch.match(samples.GOOD, job)["match_percent"]
    after = jobmatch.match(samples.GOOD + "\nKubernetes, Terraform", job)["match_percent"]
    assert after > before


def test_a_job_post_that_is_too_short_is_rejected():
    with pytest.raises(ValueError, match="at least"):
        jobmatch.match(samples.GOOD, "python developer")


def test_keywords_ignore_boilerplate_and_never_cross_punctuation():
    words = [k for k, _ in jobmatch.keywords("Candidate must have experience. Docker, Kubernetes and Terraform are required. Join our company.")]
    assert "candidate" not in words and "company" not in words
    assert not any("terraform required" in w for w in words)


def test_plural_forms_match():
    assert jobmatch.stem("apis") == jobmatch.stem("api") and jobmatch.stem("class") == "class"


def test_skill_extraction_handles_symbols_and_phrases():
    found = {s.lower() for s, _ in skills.extract_skills("Used C++, C#, Node.js and scikit-learn for machine learning.")}
    assert {"c++", "c#", "node.js", "scikit-learn", "machine learning"} <= found

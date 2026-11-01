import pytest

from resumate.checks import (contact, cliches, dates, education, experience, length, passive_voice, pages,
                             pronouns, quantified_results, repetition, spelling, strong_verbs, summary,
                             skills_section, weak_phrases)
from resumate.extract import Document


def doc(text, pages=1):
    return Document(text, pages, "text")


def bullets(*lines):
    return "\n".join("• " + line for line in lines)


def test_quantified_results_counts_measures_and_ignores_years_and_dates():
    text = bullets("Built an API serving 120,000 requests a day", "Cut load time by 38%", "Worked in 2021 on a project",
                   "Joined the team in Jan 2022 as an engineer", "Saved $4,000 a month")
    f = quantified_results(doc(text))
    assert "3 of 5" in f.summary
    assert f.score == pytest.approx(10.0)             # 60% is above the 40% target
    assert any("Worked in 2021" in e for e in f.evidence)


def test_quantified_results_scores_in_proportion():
    lines = bullets(*[f"Did thing {i} with {i + 10}%" if i < 1 else f"Handled thing {i} for the team" for i in range(10)])
    assert 0 < quantified_results(doc(lines)).score < 10


def test_strong_verbs_compare_the_first_word_only():
    f = strong_verbs(doc(bullets("Built a service", "Reduced monthly costs", "Led a team", "Was part of a group", "Responsible for tests")))
    assert "3 of 5" in f.summary and f.evidence[0].startswith("Opens with")


def test_weak_phrases_and_stock_phrases_are_found_as_whole_phrases():
    assert weak_phrases(doc("Responsible for the build. Worked on the API.")).score < 6
    assert weak_phrases(doc("Built the API and the build tools.")).score == 6
    assert cliches(doc("A hard-working team player who is a self-starter.")).score < 6
    assert cliches(doc("Built a plan for the team.")).score == 6


def test_repetition_flags_repeated_sentences_and_overused_openers():
    same = "Built a fast service for the team."
    assert repetition(doc(f"{same} Then more. {same}")).score < 6
    four = bullets("Built a tool", "Built a page", "Built a test", "Built a plan", "Led a team")
    assert repetition(doc(four)).score < 6


def test_length_is_best_between_400_and_700_words():
    best = length(doc("word " * 500)).score
    assert best == 8 and length(doc("word " * 100)).score < 2 and length(doc("word " * 1200)).score == 0
    assert 0 < length(doc("word " * 300)).score < 8


def test_pages_allow_two():
    assert pages(doc("x", 2)).score == 4 and pages(doc("x", 3)).score == 2 and pages(doc("x", 5)).score == 0


def test_passive_voice_finds_passives_but_not_active_or_adjective_use():
    assert passive_voice(doc("The API was built by the team.")).score < 5
    assert passive_voice(doc("The report was written last week.")).score < 5
    assert passive_voice(doc("I built the API. She is motivated and interested in data.")).score == 5


def test_pronouns_only_first_person():
    assert pronouns(doc("I built my own tools for me and myself.")).score == 0
    assert pronouns(doc("The system handles its own cache; it is fast.")).score == 4


def test_spelling_flags_real_misspellings_but_not_tools_or_urls():
    text = "Developed a recieve system with tensorflow and django. See github.com/ashaverma and visit https://x.io/abc."
    f = spelling(doc(text * 3))
    assert any("recieve" in e for e in f.evidence) and not any("django" in e or "ashaverma" in e for e in f.evidence)


def test_dates_need_two_and_flag_mixed_month_styles():
    assert dates(doc("Jun 2022 - Present, Jan 2021 - May 2022")).score == 4
    assert dates(doc("Jun 2022 - Present, 01/2021 - 05/2022")).score == 2
    assert dates(doc("no dates here")).score == 0
    assert dates(doc("Jun 2022 - Present. Degree 2018 - 2022")).score == 4


def test_contact_details_are_scored_one_by_one():
    full = "asha@example.com +91 98765 43210 linkedin.com/in/asha"
    assert contact(doc(full)).score == 8
    assert contact(doc("asha@example.com")).score == 3
    assert contact(doc("call 555-123-4567")).score == 2
    assert contact(doc("github.com/asha")).score == 3


@pytest.mark.parametrize("check,heading", [(education, "Education"), (experience, "Work Experience"), (experience, "PROJECTS"),
                                           (skills_section, "Technical Skills"), (summary, "Professional Summary")])
def test_section_headings_are_recognised_in_any_case(check, heading):
    assert check(doc(f"Name\n{heading}\nsomething here\n")).score > 0
    assert check(doc("Name\nnothing relevant\n")).score == 0


def test_inline_heading_with_a_colon_counts():
    assert skills_section(doc("Skills: Python, SQL, Docker")).score > 0


def test_small_counts_with_a_noun_are_results_too():
    f = quantified_results(doc(bullets("Led a team of 4 engineers on the migration", "Mentored 3 interns each summer",
                                       "Handled the team for the project", "Kept the build green every week")))
    assert "2 of 4" in f.summary

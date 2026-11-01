import samples
from resumate.extract import read_document
from resumate.highlight import render
from resumate.scoring import analyze


def lines_of(text):
    doc = read_document("r.txt", text.encode())
    return render(doc.text, analyze(doc).findings)


def test_clean_lines_are_not_flagged_and_flagged_lines_are():
    text = samples.GOOD.replace("Developed a Django dashboard", "Responsible for helping with a Django dashboard")
    lines = lines_of(text)
    by_text = {str(l["html"]): l for l in lines}
    assert lines[0]["flags"] == ""                                       # the name line
    flagged = next(l for l in lines if "Django dashboard" in str(l["html"]))
    assert "weak" in flagged["flags"].split() and '<mark data-f="weak">Responsible for</mark>' in str(flagged["html"])
    assert len(by_text) > 10


def test_words_from_the_resume_are_escaped_even_inside_marks():
    text = samples.GOOD.replace("Built a REST API", "Responsible for <b>bold</b> & <script>x</script> API")
    html = " ".join(str(l["html"]) for l in lines_of(text))
    assert "<script>" not in html and "&lt;script&gt;" in html and "&amp;" in html


def test_headings_are_marked():
    lines = lines_of(samples.GOOD)
    assert [l for l in lines if l["heading"]] and all(not l["heading"] for l in lines if "Flask" in str(l["html"]) and l["flags"] == "")


def test_every_word_flag_points_at_a_check_that_listed_it():
    doc = read_document("r.txt", samples.WEAK.encode())
    report = analyze(doc)
    keys_with_marks = {f.key for f in report.findings if f.lines or f.words}
    flagged = {k for l in render(doc.text, report.findings) for k in l["flags"].split()}
    assert flagged and flagged <= keys_with_marks

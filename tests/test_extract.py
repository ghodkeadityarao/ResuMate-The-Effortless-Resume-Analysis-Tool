import pytest

import samples
from resumate.extract import MAX_BYTES, UnreadableFile, read_document


@pytest.mark.parametrize("name,data", [("a.txt", samples.text_bytes()), ("a.docx", samples.docx_bytes()), ("a.pdf", samples.pdf_bytes())])
def test_every_format_gives_the_same_words(name, data):
    doc = read_document(name, data)
    assert "asha.verma@example.com" in doc.text and "Flask" in doc.text and doc.pages >= 1


def test_format_comes_from_the_content_not_the_name():
    assert read_document("resume", samples.pdf_bytes()).kind == "pdf"
    assert read_document("resume.pdf", samples.docx_bytes()).kind == "docx"
    assert read_document("resume.docx", samples.text_bytes()).kind == "text"


def test_bullets_are_unified_and_page_marks_removed():
    doc = read_document("a.txt", ("● one two three four five six\n seven eight nine ten eleven twelve\x0c" + "filler " * 30).encode())
    assert doc.text.count("•") == 2 and "\x0c" not in doc.text


@pytest.mark.parametrize("data,words", [(b"", "empty"), (b"\xd0\xcf\x11\xe0" + b"0" * 50, "docx"), (b"\x00\x01\x02" * 100, "not supported"),
                                         (b"too short", "30 words"), (b"%PDF-1.4 not really a pdf", "could not be read")])
def test_unreadable_files_get_a_plain_message(data, words):
    with pytest.raises(UnreadableFile, match=words):
        read_document("x", data)


def test_oversize_files_are_refused():
    with pytest.raises(UnreadableFile, match="MB"):
        read_document("x.txt", b"a " * MAX_BYTES)


def test_a_pdf_with_no_text_is_reported_as_unreadable_not_empty_text():
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    pdf.rect(10, 10, 50, 50)
    with pytest.raises(UnreadableFile, match="30 words"):
        read_document("scan.pdf", bytes(pdf.output()))

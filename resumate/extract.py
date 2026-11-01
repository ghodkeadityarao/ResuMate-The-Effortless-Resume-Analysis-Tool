"""Read the text of an uploaded file (PDF, Word or plain text) from its bytes.

Nothing is written to disk. The format is decided from the content, not the file name.
"""
import io
import re
import zipfile
from dataclasses import dataclass

MAX_BYTES = 5 * 1024 * 1024
WORDS_PER_PAGE = 500                    # used to estimate pages when a format has no page count


class UnreadableFile(ValueError):
    """The upload cannot be turned into resume text; the message says why in plain words."""


@dataclass
class Document:
    text: str
    pages: int
    kind: str                           # "pdf", "docx" or "text"


def read_document(name, data):
    if not data:
        raise UnreadableFile("The file is empty.")
    if len(data) > MAX_BYTES:
        raise UnreadableFile(f"The file is larger than {MAX_BYTES // 1024 // 1024} MB.")
    if data.startswith(b"%PDF"):
        doc = _pdf(data)
    elif data.startswith(b"PK") and _is_docx(data):
        doc = _docx(data)
    elif data.startswith(b"\xd0\xcf\x11\xe0"):
        raise UnreadableFile("Old .doc files are not supported. Save the resume as .docx or PDF and upload that.")
    elif b"\x00" in data[:2000]:
        raise UnreadableFile("That file type is not supported. Upload a PDF, a Word (.docx) file or plain text.")
    else:
        doc = Document(_decode(data), 0, "text")
    doc.text = clean(doc.text)
    if len(doc.text.split()) < 30:
        raise UnreadableFile("Fewer than 30 words could be read. If the resume is a scan or an image, "
                             "export a text version (PDF or Word) and upload that.")
    if doc.pages == 0:
        doc.pages = max(1, -(-len(doc.text.split()) // WORDS_PER_PAGE))
    return doc


def _decode(data):
    for encoding in ("utf-8", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("latin-1")


def _is_docx(data):
    try:
        return "word/document.xml" in zipfile.ZipFile(io.BytesIO(data)).namelist()
    except zipfile.BadZipFile:
        return False


def _pdf(data):
    from pdfminer.high_level import extract_text
    from pdfminer.pdfdocument import PDFPasswordIncorrect
    from pdfminer.pdfpage import PDFPage
    try:
        text = extract_text(io.BytesIO(data))
        pages = sum(1 for _ in PDFPage.get_pages(io.BytesIO(data)))
    except PDFPasswordIncorrect:
        raise UnreadableFile("The PDF is password protected. Remove the password and upload it again.")
    except Exception:
        raise UnreadableFile("The PDF could not be read. It may be damaged; try exporting it again.")
    return Document(text, pages, "pdf")


def _docx(data):
    import docx
    try:
        document = docx.Document(io.BytesIO(data))
    except Exception:
        raise UnreadableFile("The Word file could not be read. It may be damaged; try saving it again.")
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.extend(cell.text for cell in row.cells)
    return Document("\n".join(parts), 0, "docx")


BULLET_CHARS = "•●▪■◦○▫►▸‣⁃∙·➢➤✓✔"


def clean(text):
    """Tidy extracted text: one bullet character, no page-break marks, no stray blank space."""
    text = text.replace("\x0c", "\n").replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    text = re.sub("[" + re.escape(BULLET_CHARS) + "]", "•", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

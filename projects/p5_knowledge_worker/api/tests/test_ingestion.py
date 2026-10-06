import io
import zipfile

import pymupdf
import pytest
from docx import Document as DocxDocument

from knowledge_worker.core.exceptions import UnsupportedFileError
from knowledge_worker.ingestion.chunker import chunk_sections, split_sentences
from knowledge_worker.ingestion.parsers import ParseError, Section, parse_document
from knowledge_worker.services.document_service import detect_format


def count_words(text: str) -> int:
    return len(text.split())


def make_pdf(pages: list[str], password: str | None = None) -> bytes:
    doc = pymupdf.open()
    for text in pages:
        doc.new_page().insert_text((72, 72), text)
    if password:
        return doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw=password,
                           user_pw=password)
    return doc.tobytes()


def make_docx() -> bytes:
    doc = DocxDocument()
    doc.add_heading("Leave Policy", level=1)
    doc.add_paragraph("Employees receive 20 days of annual leave.")
    doc.add_heading("Remote Work", level=1)
    doc.add_paragraph("Remote work is allowed two days a week.")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "Grade", "Days"
    table.cell(1, 0).text, table.cell(1, 1).text = "A", "25"
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


class TestChunker:
    def test_splits_on_danda_and_period(self):
        assert split_sentences("প্রথম বাক্য। দ্বিতীয় বাক্য। Third one. Fourth!") == [
            "প্রথম বাক্য।", "দ্বিতীয় বাক্য।", "Third one.", "Fourth!",
        ]

    def test_respects_budget_and_overlaps(self):
        text = " ".join(f"Sentence number {i} has five words." for i in range(40))
        chunks = chunk_sections([Section(text, page=3)], max_tokens=30, overlap_tokens=10,
                                count=count_words)
        assert len(chunks) > 1
        assert all(c.token_count <= 30 for c in chunks)
        assert all(c.page == 3 for c in chunks)
        # The last sentences of one chunk start the next.
        first_tail = chunks[0].text.split(". ")[-1]
        assert chunks[1].text.startswith(first_tail.rstrip("."))

    def test_long_sentence_is_split_on_words(self):
        chunks = chunk_sections([Section("word " * 95)], max_tokens=40, overlap_tokens=5,
                                count=count_words)
        assert [c.token_count for c in chunks] == [40, 40, 15]

    def test_chunks_do_not_cross_sections(self):
        chunks = chunk_sections(
            [Section("Page one text.", page=1), Section("Page two text.", page=2)],
            max_tokens=100, overlap_tokens=10, count=count_words,
        )
        assert [(c.page, c.text) for c in chunks] == [(1, "Page one text."), (2, "Page two text.")]

    def test_overlap_must_be_smaller_than_budget(self):
        with pytest.raises(ValueError):
            chunk_sections([Section("x")], max_tokens=10, overlap_tokens=10)


class TestParsers:
    def test_pdf_keeps_page_numbers(self):
        sections = parse_document(make_pdf(["Leave policy text.", "", "Remote work text."]), "pdf")
        assert [(s.page, s.text) for s in sections] == [(1, "Leave policy text."),
                                                       (3, "Remote work text.")]

    def test_password_protected_pdf(self):
        with pytest.raises(ParseError, match="password"):
            parse_document(make_pdf(["secret"], password="pw"), "pdf")

    def test_scanned_or_empty_pdf(self):
        with pytest.raises(ParseError, match="OCR"):
            parse_document(make_pdf(["", ""]), "pdf")

    def test_damaged_pdf(self):
        with pytest.raises(ParseError, match="damaged"):
            parse_document(b"%PDF-1.7 garbage", "pdf")

    def test_docx_headings_and_tables(self):
        sections = parse_document(make_docx(), "docx")
        assert [(s.heading, s.text) for s in sections] == [
            ("Leave Policy", "Employees receive 20 days of annual leave."),
            ("Remote Work", "Remote work is allowed two days a week."),
            ("Table", "Grade | Days\nA | 25"),
        ]

    def test_markdown_headings(self):
        md = "Intro line\n# ছুটি\nবছরে ২০ দিন।\n## Remote ##\nTwo days.".encode()
        sections = parse_document(md, "md")
        assert [(s.heading, s.text) for s in sections] == [
            (None, "Intro line"), ("ছুটি", "বছরে ২০ দিন।"), ("Remote", "Two days."),
        ]

    def test_html_drops_chrome_and_nested_duplicates(self):
        html = b"""<html><head><script>x()</script></head><body><nav>Menu</nav>
            <h1>Policy</h1><p>First.</p><ul><li><p>Nested once.</p></li></ul></body></html>"""
        sections = parse_document(html, "html")
        assert [(s.heading, s.text) for s in sections] == [("Policy", "First.\nNested once.")]


class TestDetectFormat:
    def test_by_content_not_extension(self):
        assert detect_format("report.txt", make_pdf(["x"])) == "pdf"
        assert detect_format("report.bin", make_docx()) == "docx"

    def test_text_flavours_by_extension(self):
        assert detect_format("a.md", b"# hi") == "md"
        assert detect_format("a.HTM", b"<p>hi</p>") == "html"
        assert detect_format("a.txt", "বাংলা".encode()) == "txt"

    def test_rejects_non_docx_zip(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("hello.txt", "hi")
        with pytest.raises(UnsupportedFileError, match="docx"):
            detect_format("a.zip", buf.getvalue())

    def test_rejects_non_utf8_text(self):
        with pytest.raises(UnsupportedFileError, match="UTF-8"):
            detect_format("a.txt", "café".encode("latin-1"))

    def test_rejects_unknown_type(self):
        with pytest.raises(UnsupportedFileError, match="Unsupported"):
            detect_format("image.png", b"\x89PNG\r\n")

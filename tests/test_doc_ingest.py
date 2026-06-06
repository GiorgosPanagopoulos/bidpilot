from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.ingestion.doc_parser import parse_pdf_to_chunks


def _make_mock_reader(pages_text: list[str]) -> MagicMock:
    pages = []
    for text in pages_text:
        page = MagicMock()
        page.extract_text.return_value = text
        pages.append(page)
    reader = MagicMock()
    reader.pages = pages
    return reader


def test_doc_ingest_chunks_carry_tender_id():
    tender_id = "tender-001"
    page_text = (
        "Άρθρο 5\n\n"
        "The contractor must provide civil engineering services for the project.\n\n"
        "Additional technical specifications apply as described in Annex I."
    )
    mock_reader = _make_mock_reader([page_text])

    with patch("app.ingestion.doc_parser.pypdf.PdfReader", return_value=mock_reader):
        chunks = parse_pdf_to_chunks(b"fake-pdf", tender_id)

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["metadata"]["tender_id"] == tender_id
        assert "locator" in chunk["metadata"]


def test_doc_ingest_chunks_locator_from_heading():
    tender_id = "tender-002"
    page_text = (
        "Article 3\n\n"
        "Financial requirements: the bidder must demonstrate sufficient turnover.\n\n"
        "A minimum annual turnover of EUR 2,000,000 is required."
    )
    mock_reader = _make_mock_reader([page_text])

    with patch("app.ingestion.doc_parser.pypdf.PdfReader", return_value=mock_reader):
        chunks = parse_pdf_to_chunks(b"fake-pdf", tender_id)

    locators = {c["metadata"]["locator"] for c in chunks}
    assert any("Article 3" in loc for loc in locators)


def test_doc_ingest_chunks_fallback_to_page_number():
    tender_id = "tender-003"
    page_text = (
        "This page has no recognisable section heading.\n\n"
        "It contains general tender information spread across multiple lines.\n\n"
        "The contracting authority is located in Athens."
    )
    mock_reader = _make_mock_reader([page_text])

    with patch("app.ingestion.doc_parser.pypdf.PdfReader", return_value=mock_reader):
        chunks = parse_pdf_to_chunks(b"fake-pdf", tender_id)

    assert any(c["metadata"]["locator"].startswith("p.") for c in chunks)


def test_doc_ingest_short_chunks_filtered():
    tender_id = "tender-004"
    page_text = "OK\n\nThis paragraph is long enough to be included as a chunk in the output.\n\nX"
    mock_reader = _make_mock_reader([page_text])

    with patch("app.ingestion.doc_parser.pypdf.PdfReader", return_value=mock_reader):
        chunks = parse_pdf_to_chunks(b"fake-pdf", tender_id)

    # Short strings like "OK" and "X" must be filtered out
    for chunk in chunks:
        assert len(chunk["text"]) >= 60


def test_doc_ingest_multipage_produces_chunks_per_page():
    tender_id = "tender-005"
    pages = [
        "Article 1\n\nFirst section with substantial technical content about requirements.\n\nMore details here.",
        "Article 2\n\nSecond section with financial qualification requirements for the bid.\n\nFurther details.",
    ]
    mock_reader = _make_mock_reader(pages)

    with patch("app.ingestion.doc_parser.pypdf.PdfReader", return_value=mock_reader):
        chunks = parse_pdf_to_chunks(b"fake-pdf", tender_id)

    assert len(chunks) >= 2

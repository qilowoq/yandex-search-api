import pytest

from yandex_search._xml_parser import (
    parse_gen_search_json,
    parse_image_search_xml,
    parse_web_search_xml,
)
from yandex_search.exceptions import XMLParseError


class TestParseWebSearchXml:
    def test_basic_fields(self, web_xml: bytes):
        result = parse_web_search_xml(web_xml)
        assert result.query == "python dataclasses"
        assert result.page == 0
        assert result.request_id == "1234567890-abcdef"
        assert result.total_found == 12345
        assert result.total_found_human == "found 12345 results"

    def test_groups(self, web_xml: bytes):
        result = parse_web_search_xml(web_xml)
        assert len(result.groups) == 2

        g1 = result.groups[0]
        assert g1.category == "docs.python.org"
        assert g1.doc_count == 42
        assert len(g1.documents) == 1

        g2 = result.groups[1]
        assert g2.category == "realpython.com"
        assert g2.doc_count == 15

    def test_documents_flat(self, web_xml: bytes):
        result = parse_web_search_xml(web_xml)
        docs = result.documents
        assert len(docs) == 2
        assert docs[0].url == "https://docs.python.org/3/library/dataclasses.html"
        assert docs[1].url == "https://realpython.com/python-data-classes/"

    def test_document_fields(self, web_xml: bytes):
        result = parse_web_search_xml(web_xml)
        doc = result.documents[0]
        assert doc.domain == "docs.python.org"
        assert doc.title == "**Python** **dataclasses** module"
        assert doc.headline == "Official documentation for dataclasses"
        assert doc.modified_time == "20240301T000000"
        assert doc.size == 54321
        assert doc.charset == "utf-8"
        assert doc.language == "en"
        assert doc.mime_type == "text/html"
        assert doc.saved_copy_url == "https://yandexwebcache.net/doc1"
        assert doc.doc_id == "doc1"

    def test_passages(self, web_xml: bytes):
        result = parse_web_search_xml(web_xml)
        doc = result.documents[0]
        assert len(doc.passages) == 2

        p1 = doc.passages[0]
        assert "dataclasses" in p1.text
        assert "**dataclasses**" in p1.highlighted_text

        p2 = doc.passages[1]
        assert "@dataclass" in p2.text
        assert "**@dataclass**" in p2.highlighted_text

    def test_document_without_optional_fields(self, web_xml: bytes):
        result = parse_web_search_xml(web_xml)
        doc = result.documents[1]
        assert doc.modified_time is None
        assert doc.saved_copy_url is None

    def test_invalid_xml(self):
        with pytest.raises(XMLParseError):
            parse_web_search_xml(b"not xml at all")

    def test_empty_response(self):
        xml = b'<?xml version="1.0"?><yandexsearch version="1.0"></yandexsearch>'
        result = parse_web_search_xml(xml)
        assert result.query == ""
        assert result.groups == []
        assert result.documents == []


class TestParseImageSearchXml:
    def test_basic_fields(self, image_xml: bytes):
        result = parse_image_search_xml(image_xml)
        assert result.query == "cute cats"
        assert result.page == 0
        assert result.request_id == "img-req-12345"
        assert result.total_found == 99999

    def test_documents(self, image_xml: bytes):
        result = parse_image_search_xml(image_xml)
        assert len(result.documents) == 2

        doc = result.documents[0]
        assert doc.url == "https://example.com/cats/page1"
        assert doc.domain == "example.com"
        assert doc.title == "Cute **cats** photo gallery"
        assert doc.image_url == "https://example.com/images/cat1.jpg"
        assert doc.thumbnail_url == "https://im0-tub.yandex.net/i?id=cat1-thumb"
        assert doc.width == 200
        assert doc.height == 150
        assert doc.size == 245000
        assert doc.mime_type == "image/jpeg"
        assert doc.doc_id == "img1"


class TestParseGenSearchJson:
    def test_basic_fields(self, gen_json: dict):
        result = parse_gen_search_json(gen_json)
        assert "высокоуровневый" in result.message.content
        assert result.message.role == "ROLE_ASSISTANT"
        assert result.is_answer_rejected is False
        assert result.is_bullet_answer is False
        assert result.problematic_answer is False
        assert result.fixed_misspell_query is None

    def test_sources(self, gen_json: dict):
        result = parse_gen_search_json(gen_json)
        assert len(result.sources) == 3
        assert result.sources[0].url == "https://ru.wikipedia.org/wiki/Python"
        assert result.sources[0].used is True
        assert result.sources[2].used is False

    def test_search_queries(self, gen_json: dict):
        result = parse_gen_search_json(gen_json)
        assert len(result.search_queries) == 1
        assert result.search_queries[0].text == "что такое Python язык программирования"
        assert result.search_queries[0].req_id == "sq-123"

    def test_hints(self, gen_json: dict):
        result = parse_gen_search_json(gen_json)
        assert result.hints == ["история Python", "Python vs Java"]

    def test_empty_response(self):
        result = parse_gen_search_json({})
        assert result.message.content == ""
        assert result.sources == []
        assert result.hints == []

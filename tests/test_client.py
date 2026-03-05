import base64
import json
from pathlib import Path

import httpx
import pytest
import respx

from yandex_search import (
    AuthenticationError,
    YandexSearch,
    YandexSearchError,
)
from yandex_search.exceptions import BadRequestError, ServerError
from yandex_search.models.enums import ContentFormat, SearchType
from yandex_search.models.web import Document

FIXTURES_DIR = Path(__file__).parent / "fixtures"
API_KEY = "test-api-key-12345"
FOLDER_ID = "b1g-test-folder"
BASE_URL = "https://searchapi.api.cloud.yandex.net/v2"


@pytest.fixture
def web_raw_data() -> str:
    xml_bytes = (FIXTURES_DIR / "web_response.xml").read_bytes()
    return base64.b64encode(xml_bytes).decode()


@pytest.fixture
def image_raw_data() -> str:
    xml_bytes = (FIXTURES_DIR / "image_response.xml").read_bytes()
    return base64.b64encode(xml_bytes).decode()


@pytest.fixture
def gen_response_data() -> dict:
    return json.loads((FIXTURES_DIR / "gen_response.json").read_text())


class TestClientInit:
    def test_requires_api_key(self):
        with pytest.raises(AuthenticationError, match="API key is required"):
            YandexSearch()

    def test_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("YANDEX_SEARCH_API_KEY", "env-key")
        client = YandexSearch()
        assert client._api_key == "env-key"
        client.close()

    def test_folder_id_optional(self):
        client = YandexSearch(api_key=API_KEY)
        assert client._folder_id is None
        client.close()

    def test_folder_id_from_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("YANDEX_FOLDER_ID", "env-folder")
        client = YandexSearch(api_key=API_KEY)
        assert client._folder_id == "env-folder"
        client.close()

    def test_context_manager(self):
        with YandexSearch(api_key=API_KEY) as client:
            assert client._api_key == API_KEY


class TestWebSearch:
    @respx.mock
    def test_search_success(self, web_raw_data: str):
        route = respx.post(f"{BASE_URL}/web/search").mock(
            return_value=httpx.Response(200, json={"rawData": web_raw_data})
        )
        with YandexSearch(api_key=API_KEY) as client:
            result = client.search("python dataclasses")

        assert route.called
        assert result.query == "python dataclasses"
        assert len(result.documents) == 2
        assert result.documents[0].domain == "docs.python.org"

    @respx.mock
    def test_search_sends_correct_body(self, web_raw_data: str):
        route = respx.post(f"{BASE_URL}/web/search").mock(
            return_value=httpx.Response(200, json={"rawData": web_raw_data})
        )
        with YandexSearch(api_key=API_KEY) as client:
            client.search(
                "test query",
                search_type=SearchType.COM,
                page=2,
                max_passages=5,
            )

        body = json.loads(route.calls[0].request.content)
        assert body["query"]["queryText"] == "test query"
        assert body["query"]["searchType"] == "SEARCH_TYPE_COM"
        assert body["query"]["page"] == 2
        assert body["maxPassages"] == 5

    @respx.mock
    def test_search_auth_header(self, web_raw_data: str):
        respx.post(f"{BASE_URL}/web/search").mock(
            return_value=httpx.Response(200, json={"rawData": web_raw_data})
        )
        with YandexSearch(api_key=API_KEY) as client:
            client.search("test")

        request = respx.calls[0].request
        assert request.headers["Authorization"] == f"Api-Key {API_KEY}"


class TestImageSearch:
    @respx.mock
    def test_search_images_success(self, image_raw_data: str):
        respx.post(f"{BASE_URL}/image/search").mock(
            return_value=httpx.Response(200, json={"rawData": image_raw_data})
        )
        with YandexSearch(api_key=API_KEY) as client:
            result = client.search_images("cute cats")

        assert result.query == "cute cats"
        assert len(result.documents) == 2
        assert result.documents[0].image_url == "https://example.com/images/cat1.jpg"

    @respx.mock
    def test_search_images_with_size_string(self, image_raw_data: str):
        route = respx.post(f"{BASE_URL}/image/search").mock(
            return_value=httpx.Response(200, json={"rawData": image_raw_data})
        )
        with YandexSearch(api_key=API_KEY) as client:
            client.search_images("test", size="LARGE")

        body = json.loads(route.calls[0].request.content)
        assert body["imageSpec"]["size"] == "IMAGE_SIZE_LARGE"


class TestGenSearch:
    @respx.mock
    def test_gen_search_success(self, gen_response_data: dict):
        respx.post(f"{BASE_URL}/gen/search").mock(
            return_value=httpx.Response(200, json=gen_response_data)
        )
        with YandexSearch(api_key=API_KEY, folder_id=FOLDER_ID) as client:
            result = client.gen_search("Что такое Python?")

        assert "высокоуровневый" in result.message.content
        assert len(result.sources) == 3
        assert result.hints == ["история Python", "Python vs Java"]

    def test_gen_search_requires_folder_id(self):
        with YandexSearch(api_key=API_KEY) as client, pytest.raises(
            YandexSearchError, match="folder_id is required"
        ):
            client.gen_search("test")

    @respx.mock
    def test_gen_search_folder_id_override(self, gen_response_data: dict):
        route = respx.post(f"{BASE_URL}/gen/search").mock(
            return_value=httpx.Response(200, json=gen_response_data)
        )
        with YandexSearch(api_key=API_KEY, folder_id="default-folder") as client:
            client.gen_search("test", folder_id="override-folder")

        body = json.loads(route.calls[0].request.content)
        assert body["folderId"] == "override-folder"

    @respx.mock
    def test_gen_search_folder_id_from_arg(self, gen_response_data: dict):
        route = respx.post(f"{BASE_URL}/gen/search").mock(
            return_value=httpx.Response(200, json=gen_response_data)
        )
        with YandexSearch(api_key=API_KEY) as client:
            client.gen_search("test", folder_id="arg-folder")

        body = json.loads(route.calls[0].request.content)
        assert body["folderId"] == "arg-folder"

    @respx.mock
    def test_gen_search_with_history(self, gen_response_data: dict):
        route = respx.post(f"{BASE_URL}/gen/search").mock(
            return_value=httpx.Response(200, json=gen_response_data)
        )
        with YandexSearch(api_key=API_KEY, folder_id=FOLDER_ID) as client:
            client.gen_search(
                "Tell me more",
                history=[
                    {"role": "user", "content": "What is Python?"},
                    {"role": "assistant", "content": "Python is a language."},
                ],
            )

        body = json.loads(route.calls[0].request.content)
        messages = body["messages"]
        assert len(messages) == 3
        assert messages[0]["role"] == "ROLE_USER"
        assert messages[1]["role"] == "ROLE_ASSISTANT"
        assert messages[2]["role"] == "ROLE_USER"
        assert messages[2]["content"] == "Tell me more"


class TestErrorHandling:
    @respx.mock
    def test_400_error(self):
        respx.post(f"{BASE_URL}/web/search").mock(
            return_value=httpx.Response(400, json={"message": "Bad query"})
        )
        with YandexSearch(api_key=API_KEY) as client, pytest.raises(
            BadRequestError, match="Bad query"
        ):
            client.search("test")

    @respx.mock
    def test_401_error(self):
        respx.post(f"{BASE_URL}/web/search").mock(
            return_value=httpx.Response(401, json={"message": "Invalid key"})
        )
        with YandexSearch(api_key=API_KEY) as client, pytest.raises(
            AuthenticationError, match="Invalid key"
        ):
            client.search("test")

    @respx.mock
    def test_500_error(self):
        respx.post(f"{BASE_URL}/web/search").mock(
            return_value=httpx.Response(500, content=b"Internal Server Error")
        )
        with YandexSearch(api_key=API_KEY) as client, pytest.raises(ServerError):
            client.search("test")


CACHED_HTML = "<html><body><h1>Title</h1><p>Hello <b>world</b></p></body></html>"
CACHED_URL = "https://yandexwebcache.net/doc1"


class TestFetchCached:
    @respx.mock
    def test_fetch_cached_markdown(self):
        respx.get(CACHED_URL).mock(
            return_value=httpx.Response(200, text=CACHED_HTML)
        )
        doc = Document(url="https://example.com", domain="example.com", title="Test",
                       saved_copy_url=CACHED_URL)
        with YandexSearch(api_key=API_KEY) as client:
            result = client.fetch_cached(doc)

        assert "Title" in result
        assert "**world**" in result
        assert "<" not in result

    @respx.mock
    def test_fetch_cached_html(self):
        respx.get(CACHED_URL).mock(
            return_value=httpx.Response(200, text=CACHED_HTML)
        )
        doc = Document(url="https://example.com", domain="example.com", title="Test",
                       saved_copy_url=CACHED_URL)
        with YandexSearch(api_key=API_KEY) as client:
            result = client.fetch_cached(doc, content_format=ContentFormat.HTML)

        assert "<h1>Title</h1>" in result

    @respx.mock
    def test_fetch_cached_text(self):
        respx.get(CACHED_URL).mock(
            return_value=httpx.Response(200, text=CACHED_HTML)
        )
        doc = Document(url="https://example.com", domain="example.com", title="Test",
                       saved_copy_url=CACHED_URL)
        with YandexSearch(api_key=API_KEY) as client:
            result = client.fetch_cached(doc, content_format="text")

        assert "Title" in result
        assert "Hello world" in result
        assert "<" not in result

    def test_fetch_cached_no_url(self):
        doc = Document(url="https://example.com", domain="example.com", title="Test")
        with YandexSearch(api_key=API_KEY) as client, pytest.raises(
            YandexSearchError, match="no saved_copy_url"
        ):
            client.fetch_cached(doc)

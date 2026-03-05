from __future__ import annotations

import base64
import json
import os
import re
from typing import NoReturn

from markdownify import markdownify as md

from ._xml_parser import parse_gen_search_json, parse_image_search_xml, parse_web_search_xml
from .exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    YandexSearchError,
)
from .models.enums import (
    ContentFormat,
    FamilyMode,
    FixTypoMode,
    GroupMode,
    ImageColor,
    ImageFormat,
    ImageOrientation,
    ImageSize,
    L10n,
    MessageRole,
    ResponseFormat,
    SearchType,
    SortMode,
    SortOrder,
)
from .models.gen import GenSearchResponse
from .models.image import ImageSearchResponse
from .models.request import (
    GenSearchRequest,
    GroupSpec,
    ImageSearchRequest,
    ImageSpec,
    Message,
    QuerySpec,
    SortSpec,
    WebSearchRequest,
)
from .models.web import WebSearchResponse

_BASE_URL = "https://searchapi.api.cloud.yandex.net/v2"

_STATUS_MAP: dict[int, type[YandexSearchError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    429: RateLimitError,
}


class _BaseClient:
    def __init__(
        self,
        api_key: str | None = None,
        folder_id: str | None = None,
        *,
        base_url: str = _BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 2,
        user_agent: str | None = None,
    ):
        self._api_key = api_key or os.environ.get("YANDEX_SEARCH_API_KEY")
        if not self._api_key:
            raise AuthenticationError(
                "API key is required. Pass api_key= or set YANDEX_SEARCH_API_KEY env var."
            )
        self._folder_id = folder_id or os.environ.get("YANDEX_FOLDER_ID")
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._user_agent = user_agent

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Api-Key {self._api_key}",
            "Content-Type": "application/json",
        }

    # --- Request body builders ---

    def _build_web_search_body(
        self,
        query: str,
        *,
        search_type: SearchType = SearchType.COM,
        family_mode: FamilyMode = FamilyMode.MODERATE,
        page: int = 0,
        fix_typo: bool = True,
        sort_mode: SortMode = SortMode.BY_RELEVANCE,
        sort_order: SortOrder | str = SortOrder.DESC,
        group_mode: GroupMode = GroupMode.DEEP,
        groups_on_page: int = 10,
        docs_in_group: int = 1,
        max_passages: int = 2,
        region: str | None = None,
        l10n: L10n | str | None = None,
        response_format: ResponseFormat | str = ResponseFormat.XML,
    ) -> dict:
        if not isinstance(sort_order, SortOrder):
            sort_order = SortOrder(f"SORT_ORDER_{sort_order.upper()}")
        if l10n is not None and not isinstance(l10n, L10n):
            l10n = L10n(f"L10N_{l10n.upper()}")
        if not isinstance(response_format, ResponseFormat):
            response_format = ResponseFormat(f"FORMAT_{response_format.upper()}")

        req = WebSearchRequest(
            query=QuerySpec(
                query_text=query,
                search_type=search_type,
                family_mode=family_mode,
                page=page,
                fix_typo_mode=FixTypoMode.ON if fix_typo else FixTypoMode.OFF,
            ),
            sort_spec=SortSpec(sort_mode=sort_mode, sort_order=sort_order),
            group_spec=GroupSpec(
                group_mode=group_mode,
                groups_on_page=groups_on_page,
                docs_in_group=docs_in_group,
            ),
            max_passages=max_passages,
            region=region,
            l10n=l10n,
            folder_id=self._folder_id,
            response_format=response_format,
            user_agent=self._user_agent,
        )
        return req.to_api_dict()

    def _build_image_search_body(
        self,
        query: str,
        *,
        search_type: SearchType = SearchType.COM,
        family_mode: FamilyMode = FamilyMode.MODERATE,
        page: int = 0,
        fix_typo: bool = True,
        format: ImageFormat | None = None,
        size: ImageSize | str | None = None,
        orientation: ImageOrientation | None = None,
        color: ImageColor | None = None,
        site: str | None = None,
        docs_on_page: int = 20,
    ) -> dict:
        if size is not None and not isinstance(size, ImageSize):
            size = ImageSize(f"IMAGE_SIZE_{size.upper()}")

        req = ImageSearchRequest(
            query=QuerySpec(
                query_text=query,
                search_type=search_type,
                family_mode=family_mode,
                page=page,
                fix_typo_mode=FixTypoMode.ON if fix_typo else FixTypoMode.OFF,
            ),
            image_spec=ImageSpec(
                format=format, size=size, orientation=orientation, color=color
            ),
            site=site,
            docs_on_page=docs_on_page,
            folder_id=self._folder_id,
            user_agent=self._user_agent,
        )
        return req.to_api_dict()

    def _build_gen_search_body(
        self,
        query: str,
        *,
        folder_id: str | None = None,
        history: list[dict[str, str]] | None = None,
        site: list[str] | None = None,
        host: list[str] | None = None,
        url: list[str] | None = None,
        fix_misspell: bool = True,
        search_type: SearchType = SearchType.COM,
        search_filters: list[dict[str, str]] | None = None,
    ) -> dict:
        resolved_folder_id = folder_id or self._folder_id
        if not resolved_folder_id:
            raise YandexSearchError(
                "folder_id is required for gen_search. "
                "Pass it to the client constructor or to gen_search() directly."
            )

        messages: list[Message] = []
        if history:
            for msg in history:
                role_str = msg.get("role", "user").upper()
                role = (
                    MessageRole.ASSISTANT
                    if role_str == "ASSISTANT"
                    else MessageRole.USER
                )
                messages.append(Message(content=msg["content"], role=role))
        messages.append(Message(content=query, role=MessageRole.USER))

        req = GenSearchRequest(
            folder_id=resolved_folder_id,
            messages=messages,
            site=site,
            host=host,
            url=url,
            fix_misspell=fix_misspell,
            search_type=search_type,
        )
        return req.to_api_dict()

    # --- Response parsers ---

    def _parse_web_response(self, data: dict) -> WebSearchResponse:
        raw = base64.b64decode(data["rawData"])
        return parse_web_search_xml(raw)

    def _parse_image_response(self, data: dict) -> ImageSearchResponse:
        raw = base64.b64decode(data["rawData"])
        return parse_image_search_xml(raw)

    def _parse_gen_response(self, data: dict) -> GenSearchResponse:
        return parse_gen_search_json(data)

    # --- Cached content ---

    @staticmethod
    def _validate_cached_url(doc: object) -> str:
        url = getattr(doc, "saved_copy_url", None)
        if not url:
            raise YandexSearchError(
                "Document has no saved_copy_url. "
                "Not all search results have a cached copy."
            )
        return url

    @staticmethod
    def _strip_yandex_cache_wrapper(html: str) -> str:
        """Remove Yandex cache wrapper, leave only the embedded page HTML.

        Cached page response contains: outer HTML, #yandex-cache-hdr block,
        then the real page as second <!doctype html>…</html>. Extract only that.
        """
        doctype_re = re.compile(r"<!doctype\s+html>", re.IGNORECASE)
        matches = list(doctype_re.finditer(html))
        if len(matches) < 2:
            return html
        start = matches[1].start()
        end_tag = "</html>"
        end_idx = html.find(end_tag, start)
        if end_idx == -1:
            return html
        return html[start : end_idx + len(end_tag)].strip()

    _NOISE_TAGS = ("script", "style", "noscript", "iframe", "svg")

    @staticmethod
    def _strip_noise_tags(html: str) -> str:
        """Remove script, style, noscript, iframe, svg and their content."""
        try:
            from lxml import html as lxml_html

            doc = lxml_html.fromstring(html)
            for tag in _BaseClient._NOISE_TAGS:
                for el in list(doc.iter(tag)):
                    el.drop_tree()  # type: ignore[union-attr]
            html = lxml_html.tostring(
                doc, encoding="unicode", method="html"
            )
        except Exception:
            pass
        # Always run regex strip (handles edge cases and fallback when lxml fails)
        for tag in _BaseClient._NOISE_TAGS:
            html = re.sub(
                rf"<{tag}[^>]*>.*?</{tag}>",
                "",
                html,
                flags=re.DOTALL | re.IGNORECASE,
            )
        return html

    @staticmethod
    def _clean_markdown(md_text: str) -> str:
        """Remove leftover noise (script/config/CSS snippets) and collapse newlines."""
        lines = md_text.split("\n")
        out: list[str] = []
        skip_patterns = (
            r"^\s*\(\(\)\s*=>",  # (() =>
            r"^\s*var\s+\w+\s*=",  # var x =
            r"function\s*\(",  # function(
            r"\.push\s*\(",  # .push(
            r"freestar\.",  # freestar
            r"dataLayer\.push",  # dataLayer
            r"gtag\s*\(",  # gtag(
            r"window\.dataLayer",  # dataLayer
            r"^\s*\);?\s*$",  # ); alone
            r"^\s*\}\s*\)\s*\(\s*\)",  # })();
            r"[\w.]+\s*=\s*[\w.]+\s*\|\|\s*\{\}",  # x = x || {}
            r"@media\s+screen",  # @media CSS
            r"^\s*[.#]?[\w-]+\s*\{",  # CSS selector {
            r"data:image/[^;]+;base64,",  # inline base64 images
        )
        compiled = [re.compile(p) for p in skip_patterns]
        for line in lines:
            if any(p.search(line) for p in compiled):
                continue
            stripped = line.strip()
            if not stripped:
                if out and out[-1].strip() == "":
                    continue
            out.append(line)
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(out))
        return text.strip()

    @staticmethod
    def _convert_html(
        html: str,
        content_format: ContentFormat | str = ContentFormat.MARKDOWN,
    ) -> str:
        if not isinstance(content_format, ContentFormat):
            content_format = ContentFormat(content_format.lower())

        html = _BaseClient._strip_yandex_cache_wrapper(html)
        html = _BaseClient._strip_noise_tags(html)

        if content_format == ContentFormat.HTML:
            return html
        if content_format == ContentFormat.TEXT:
            text = re.sub(r"<[^>]+>", "", html)
            return re.sub(r"\n{3,}", "\n\n", text).strip()
        # markdown (ATX headings: # not underlines)
        result = md(
            html,
            strip=list(_BaseClient._NOISE_TAGS),
            heading_style="ATX",
        ).strip()
        return _BaseClient._clean_markdown(result)

    # --- Error handling ---

    def _handle_error(self, status_code: int, body: bytes) -> NoReturn:
        text = body.decode("utf-8", errors="replace")
        message = text
        try:
            data = json.loads(text)
            message = data.get("message", text)
        except (json.JSONDecodeError, AttributeError):
            pass

        exc_class = _STATUS_MAP.get(status_code)
        if exc_class is RateLimitError:
            raise RateLimitError(message)
        elif exc_class:
            raise exc_class(message)
        elif status_code >= 500:
            raise ServerError(message)
        else:
            raise APIError(message, status_code=status_code, body=text)

from __future__ import annotations

import time

import httpx

from ._base_client import _BaseClient
from .exceptions import ConnectionError
from .models.enums import (
    ContentFormat,
    FamilyMode,
    GroupMode,
    ImageColor,
    ImageFormat,
    ImageOrientation,
    ImageSize,
    L10n,
    ResponseFormat,
    SearchType,
    SortMode,
    SortOrder,
)
from .models.gen import GenSearchResponse
from .models.image import ImageSearchResponse
from .models.web import WebSearchResponse


class YandexSearch(_BaseClient):
    """Synchronous client for Yandex Search API."""

    def __init__(
        self,
        api_key: str | None = None,
        folder_id: str | None = None,
        *,
        base_url: str = "https://searchapi.api.cloud.yandex.net/v2",
        timeout: float = 30.0,
        max_retries: int = 2,
        user_agent: str | None = None,
    ):
        super().__init__(
            api_key=api_key,
            folder_id=folder_id,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            user_agent=user_agent,
        )
        self._http = httpx.Client(
            headers=self._headers(),
            timeout=self._timeout,
        )

    def _request(self, path: str, body: dict) -> dict:
        url = f"{self._base_url}/{path}"
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = self._http.post(url, json=body)
                if resp.status_code >= 400:
                    self._handle_error(resp.status_code, resp.content)
                return resp.json()
            except httpx.TransportError as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    time.sleep(2**attempt * 0.5)
        raise ConnectionError(
            f"Request to {url} failed after {self._max_retries + 1} attempts"
        ) from last_exc

    def search(
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
    ) -> WebSearchResponse:
        body = self._build_web_search_body(
            query,
            search_type=search_type,
            family_mode=family_mode,
            page=page,
            fix_typo=fix_typo,
            sort_mode=sort_mode,
            sort_order=sort_order,
            group_mode=group_mode,
            groups_on_page=groups_on_page,
            docs_in_group=docs_in_group,
            max_passages=max_passages,
            region=region,
            l10n=l10n,
            response_format=response_format,
        )
        data = self._request("web/search", body)
        return self._parse_web_response(data)

    def search_images(
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
    ) -> ImageSearchResponse:
        body = self._build_image_search_body(
            query,
            search_type=search_type,
            family_mode=family_mode,
            page=page,
            fix_typo=fix_typo,
            format=format,
            size=size,
            orientation=orientation,
            color=color,
            site=site,
            docs_on_page=docs_on_page,
        )
        data = self._request("image/search", body)
        return self._parse_image_response(data)

    def gen_search(
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
    ) -> GenSearchResponse:
        body = self._build_gen_search_body(
            query,
            folder_id=folder_id,
            history=history,
            site=site,
            host=host,
            url=url,
            fix_misspell=fix_misspell,
            search_type=search_type,
            search_filters=search_filters,
        )
        data = self._request("gen/search", body)
        return self._parse_gen_response(data)

    def fetch_cached(
        self,
        doc: object,
        *,
        content_format: ContentFormat | str = ContentFormat.MARKDOWN,
    ) -> str:
        """Fetch cached page content from Yandex's saved copy.

        Args:
            doc: A Document with a saved_copy_url attribute.
            content_format: Output format — "markdown" (default), "html", or "text".
        """
        url = self._validate_cached_url(doc)
        resp = self._http.get(url)
        resp.raise_for_status()
        return self._convert_html(resp.text, content_format)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> YandexSearch:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

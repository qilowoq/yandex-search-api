from __future__ import annotations

from dataclasses import dataclass, field

from .enums import (
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


def _drop_none(d: dict) -> dict:
    """Recursively remove None values from a dict."""
    result = {}
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, dict):
            v = _drop_none(v)
        result[k] = v
    return result


@dataclass
class QuerySpec:
    query_text: str
    search_type: SearchType = SearchType.RU
    family_mode: FamilyMode = FamilyMode.MODERATE
    page: int = 0
    fix_typo_mode: FixTypoMode = FixTypoMode.ON

    def to_api_dict(self) -> dict:
        return {
            "searchType": self.search_type.value,
            "queryText": self.query_text,
            "familyMode": self.family_mode.value,
            "page": self.page,
            "fixTypoMode": self.fix_typo_mode.value,
        }


@dataclass
class SortSpec:
    sort_mode: SortMode = SortMode.BY_RELEVANCE
    sort_order: SortOrder = SortOrder.DESC

    def to_api_dict(self) -> dict:
        return {
            "sortMode": self.sort_mode.value,
            "sortOrder": self.sort_order.value,
        }


@dataclass
class GroupSpec:
    group_mode: GroupMode = GroupMode.DEEP
    groups_on_page: int = 10
    docs_in_group: int = 1

    def to_api_dict(self) -> dict:
        return {
            "groupMode": self.group_mode.value,
            "groupsOnPage": self.groups_on_page,
            "docsInGroup": self.docs_in_group,
        }


@dataclass
class ImageSpec:
    format: ImageFormat | None = None
    size: ImageSize | None = None
    orientation: ImageOrientation | None = None
    color: ImageColor | None = None

    def to_api_dict(self) -> dict:
        return _drop_none({
            "format": self.format.value if self.format else None,
            "size": self.size.value if self.size else None,
            "orientation": self.orientation.value if self.orientation else None,
            "color": self.color.value if self.color else None,
        })


@dataclass
class WebSearchRequest:
    query: QuerySpec
    sort_spec: SortSpec = field(default_factory=SortSpec)
    group_spec: GroupSpec = field(default_factory=GroupSpec)
    max_passages: int = 2
    region: str | None = None
    l10n: L10n | None = None
    folder_id: str | None = None
    response_format: ResponseFormat = ResponseFormat.XML
    user_agent: str | None = None

    def to_api_dict(self) -> dict:
        return _drop_none({
            "query": self.query.to_api_dict(),
            "sortSpec": self.sort_spec.to_api_dict(),
            "groupSpec": self.group_spec.to_api_dict(),
            "maxPassages": self.max_passages,
            "region": self.region,
            "l10n": self.l10n.value if self.l10n else None,
            "folderId": self.folder_id,
            "responseFormat": self.response_format.value,
            "userAgent": self.user_agent,
        })


@dataclass
class ImageSearchRequest:
    query: QuerySpec
    image_spec: ImageSpec = field(default_factory=ImageSpec)
    site: str | None = None
    docs_on_page: int = 20
    folder_id: str | None = None
    user_agent: str | None = None

    def to_api_dict(self) -> dict:
        d: dict = {
            "query": self.query.to_api_dict(),
            "docsOnPage": self.docs_on_page,
        }
        image_spec = self.image_spec.to_api_dict()
        if image_spec:
            d["imageSpec"] = image_spec
        if self.site:
            d["site"] = self.site
        if self.folder_id:
            d["folderId"] = self.folder_id
        if self.user_agent:
            d["userAgent"] = self.user_agent
        return d


@dataclass
class Message:
    content: str
    role: MessageRole

    def to_api_dict(self) -> dict:
        return {
            "content": self.content,
            "role": self.role.value,
        }


@dataclass
class SearchFilter:
    date: str | None = None
    lang: str | None = None
    format: str | None = None

    def to_api_dict(self) -> dict:
        return _drop_none({
            "date": self.date,
            "lang": self.lang,
            "format": self.format,
        })


@dataclass
class GenSearchRequest:
    folder_id: str
    messages: list[Message]
    site: list[str] | None = None
    host: list[str] | None = None
    url: list[str] | None = None
    fix_misspell: bool = True
    search_type: SearchType = SearchType.RU
    search_filters: list[SearchFilter] | None = None

    def to_api_dict(self) -> dict:
        d: dict = {
            "folderId": self.folder_id,
            "messages": [m.to_api_dict() for m in self.messages],
            "fixMisspell": self.fix_misspell,
            "searchType": self.search_type.value,
        }
        if self.site:
            d["site"] = self.site
        if self.host:
            d["host"] = self.host
        if self.url:
            d["url"] = self.url
        if self.search_filters:
            d["searchFilters"] = [f.to_api_dict() for f in self.search_filters]
        return d

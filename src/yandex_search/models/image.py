from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ImageDocument:
    url: str
    domain: str
    title: str
    image_url: str | None = None
    thumbnail_url: str | None = None
    width: int | None = None
    height: int | None = None
    size: int | None = None
    mime_type: str | None = None
    doc_id: str | None = None


@dataclass
class ImageSearchResponse:
    query: str
    page: int
    request_id: str
    total_found: int
    total_found_human: str
    documents: list[ImageDocument] = field(default_factory=list)

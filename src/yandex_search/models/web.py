from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Passage:
    text: str
    highlighted_text: str


@dataclass
class Document:
    url: str
    domain: str
    title: str
    headline: str | None = None
    modified_time: str | None = None
    size: int | None = None
    charset: str | None = None
    passages: list[Passage] = field(default_factory=list)
    language: str | None = None
    mime_type: str | None = None
    saved_copy_url: str | None = None
    doc_id: str | None = None


@dataclass
class Group:
    category: str
    doc_count: int
    documents: list[Document] = field(default_factory=list)


@dataclass
class WebSearchResponse:
    query: str
    page: int
    request_id: str
    total_found: int
    total_found_human: str
    groups: list[Group] = field(default_factory=list)

    @property
    def documents(self) -> list[Document]:
        """Flatten all groups into a single list of documents."""
        return [doc for group in self.groups for doc in group.documents]

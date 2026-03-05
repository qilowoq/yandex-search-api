from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GenMessage:
    content: str
    role: str


@dataclass
class Source:
    url: str
    title: str
    used: bool


@dataclass
class SearchQuery:
    text: str
    req_id: str


@dataclass
class GenSearchResponse:
    message: GenMessage
    sources: list[Source] = field(default_factory=list)
    search_queries: list[SearchQuery] = field(default_factory=list)
    fixed_misspell_query: str | None = None
    is_answer_rejected: bool = False
    is_bullet_answer: bool = False
    hints: list[str] = field(default_factory=list)
    problematic_answer: bool = False

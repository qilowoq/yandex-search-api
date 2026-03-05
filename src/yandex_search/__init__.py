"""Yandex Search API Python client."""

from .async_client import AsyncYandexSearch
from .client import YandexSearch
from .exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    ConnectionError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    ServerError,
    XMLParseError,
    YandexSearchError,
)
from .models.enums import (
    ContentFormat,
    FamilyMode,
    GroupMode,
    ImageColor,
    ImageFormat,
    ImageOrientation,
    ImageSize,
    MessageRole,
    SearchType,
    SortMode,
)
from .models.gen import GenMessage, GenSearchResponse, Source
from .models.image import ImageDocument, ImageSearchResponse
from .models.web import Document, Group, Passage, WebSearchResponse

__all__ = [
    "YandexSearch",
    "AsyncYandexSearch",
    # Exceptions
    "YandexSearchError",
    "AuthenticationError",
    "PermissionDeniedError",
    "NotFoundError",
    "BadRequestError",
    "RateLimitError",
    "ServerError",
    "APIError",
    "XMLParseError",
    "ConnectionError",
    # Enums
    "ContentFormat",
    "SearchType",
    "FamilyMode",
    "SortMode",
    "GroupMode",
    "ImageFormat",
    "ImageSize",
    "ImageOrientation",
    "ImageColor",
    "MessageRole",
    # Web search
    "WebSearchResponse",
    "Document",
    "Group",
    "Passage",
    # Image search
    "ImageSearchResponse",
    "ImageDocument",
    # Gen search
    "GenSearchResponse",
    "GenMessage",
    "Source",
]

__version__ = "0.1.0"

class YandexSearchError(Exception):
    """Base exception for all yandex_search errors."""


class AuthenticationError(YandexSearchError):
    """API key is missing or invalid (401)."""


class PermissionDeniedError(YandexSearchError):
    """Insufficient permissions (403)."""


class NotFoundError(YandexSearchError):
    """Resource not found (404)."""


class BadRequestError(YandexSearchError):
    """Invalid request parameters (400)."""


class RateLimitError(YandexSearchError):
    """Too many requests (429)."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class ServerError(YandexSearchError):
    """Yandex server error (5xx)."""


class APIError(YandexSearchError):
    """Generic API error with status code."""

    def __init__(self, message: str, status_code: int, body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class XMLParseError(YandexSearchError):
    """Failed to parse XML response."""


class ConnectionError(YandexSearchError):  # noqa: A001
    """Failed to connect after retries."""

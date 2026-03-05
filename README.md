# yandex-search-api

Python client for [Yandex Search API](https://cloud.yandex.ru/docs/yandex-search-api/) — web search, image search, and Gen Search.

## Requirements

- Python 3.11+

## Installation

```bash
pip install git+https://github.com/qilowoq/yandex-search-api.git
```

### From local repository

```bash
git clone https://github.com/qilowoq/yandex-search-api.git
cd yandex-search-api
pip install -e .
```

## Configuration

1. Create a service account in [Yandex Cloud](https://console.cloud.yandex.ru/) and obtain an API key. Yandex Search API is available by default.
2. Create API key.
3. Set environment variables (or pass keys to the constructor):

```bash
export YANDEX_SEARCH_API_KEY="your-api-key"
export YANDEX_FOLDER_ID="b1g..."   # optional, required for Gen Search
```

## Usage

### Synchronous client

```python
from yandex_search import YandexSearch

with YandexSearch() as client:
    result = client.search("python asyncio")
    for doc in result.documents:
        print(doc.title, doc.url)
```

### Asynchronous client

```python
from yandex_search import AsyncYandexSearch

async def main():
    async with AsyncYandexSearch() as client:
        result = await client.search("python asyncio")
        for doc in result.documents:
            print(doc.title, doc.url)

# asyncio.run(main())
```

### Image search

```python
from yandex_search import YandexSearch
from yandex_search.models.enums import ImageSize

with YandexSearch() as client:
    result = client.search_images("cats", docs_on_page=10)
    for img in result.documents:
        print(img.url, img.title)
```

### Gen Search (generated response)

```python
from yandex_search import YandexSearch

# YANDEX_FOLDER_ID is required for gen_search
with YandexSearch() as client:
    result = client.gen_search("how to configure nginx")
    print(result.response.text)
    for src in result.response.sources:
        print(src.url, src.title)
```

### Cached page (saved copy)

```python
from yandex_search import YandexSearch
from yandex_search.models.enums import ContentFormat

with YandexSearch() as client:
    result = client.search("python")
    doc = result.documents[0]
    if doc.saved_copy_url:
        content = client.fetch_cached(doc, content_format=ContentFormat.MARKDOWN)
        print(content)
```

## Exceptions

- `AuthenticationError` — invalid or missing API key
- `PermissionDeniedError` — no access to API/folder
- `RateLimitError` — request limit exceeded
- `BadRequestError` — invalid request parameters
- `NotFoundError` — resource not found
- `ServerError` — Yandex server error
- `ConnectionError` — network error or timeout
- `XMLParseError` — response parsing error

## Testing

Install dev dependencies, then run tests:

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Development

```bash
pip install -e ".[dev]"
ruff check src/ tests/
pytest tests/ -v
```

## License

See the LICENSE file in the repository.

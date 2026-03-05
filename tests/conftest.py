from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def web_xml() -> bytes:
    return (FIXTURES_DIR / "web_response.xml").read_bytes()


@pytest.fixture
def image_xml() -> bytes:
    return (FIXTURES_DIR / "image_response.xml").read_bytes()


@pytest.fixture
def gen_json() -> dict:
    import json

    return json.loads((FIXTURES_DIR / "gen_response.json").read_text())

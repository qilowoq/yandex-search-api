from __future__ import annotations

from lxml import etree

from .exceptions import XMLParseError
from .models.gen import GenMessage, GenSearchResponse, SearchQuery, Source
from .models.image import ImageDocument, ImageSearchResponse
from .models.web import Document, Group, Passage, WebSearchResponse


def parse_web_search_xml(xml_bytes: bytes) -> WebSearchResponse:
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        raise XMLParseError(f"Invalid XML: {exc}") from exc

    request_el = root.find("request")
    query = _text(request_el, "query", "")
    page = int(_text(request_el, "page", "0"))

    response_el = root.find("response")
    request_id = _text(response_el, "reqid", "")

    total_found = 0
    if response_el is not None:
        for found_el in response_el.findall("found"):
            try:
                total_found = int(found_el.text or "0")
                break
            except ValueError:
                pass

    total_found_human = _text(response_el, "found-human", "")

    groups: list[Group] = []
    if response_el is not None:
        grouping_el = response_el.find(".//results/grouping")
        if grouping_el is not None:
            for group_el in grouping_el.findall("group"):
                groups.append(_parse_group(group_el))

    return WebSearchResponse(
        query=query,
        page=page,
        request_id=request_id,
        total_found=total_found,
        total_found_human=total_found_human,
        groups=groups,
    )


def parse_image_search_xml(xml_bytes: bytes) -> ImageSearchResponse:
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as exc:
        raise XMLParseError(f"Invalid XML: {exc}") from exc

    request_el = root.find("request")
    query = _text(request_el, "query", "")
    page = int(_text(request_el, "page", "0"))

    response_el = root.find("response")
    request_id = _text(response_el, "reqid", "")

    total_found = 0
    if response_el is not None:
        for found_el in response_el.findall("found"):
            try:
                total_found = int(found_el.text or "0")
                break
            except ValueError:
                pass

    total_found_human = _text(response_el, "found-human", "")

    documents: list[ImageDocument] = []
    if response_el is not None:
        grouping_el = response_el.find(".//results/grouping")
        if grouping_el is not None:
            for group_el in grouping_el.findall("group"):
                for doc_el in group_el.findall("doc"):
                    documents.append(_parse_image_document(doc_el))

    return ImageSearchResponse(
        query=query,
        page=page,
        request_id=request_id,
        total_found=total_found,
        total_found_human=total_found_human,
        documents=documents,
    )


def parse_gen_search_json(data: dict) -> GenSearchResponse:
    msg_data = data.get("message", {})
    message = GenMessage(
        content=msg_data.get("content", ""),
        role=msg_data.get("role", "ROLE_ASSISTANT"),
    )

    sources = [
        Source(
            url=s.get("url", ""),
            title=s.get("title", ""),
            used=s.get("used", False),
        )
        for s in data.get("sources", [])
    ]

    search_queries = [
        SearchQuery(
            text=q.get("text", ""),
            req_id=q.get("reqId", ""),
        )
        for q in data.get("searchQueries", [])
    ]

    return GenSearchResponse(
        message=message,
        sources=sources,
        search_queries=search_queries,
        fixed_misspell_query=data.get("fixedMisspellQuery"),
        is_answer_rejected=data.get("isAnswerRejected", False),
        is_bullet_answer=data.get("isBulletAnswer", False),
        hints=data.get("hints", []),
        problematic_answer=data.get("problematicAnswer", False),
    )


# --- Internal helpers ---


def _parse_group(group_el: etree._Element) -> Group:
    categ_el = group_el.find("categ")
    category = categ_el.get("name", "") if categ_el is not None else ""
    doc_count = int(_text(group_el, "doccount", "0"))
    documents = [_parse_document(doc_el) for doc_el in group_el.findall("doc")]
    return Group(category=category, doc_count=doc_count, documents=documents)


def _parse_document(doc_el: etree._Element) -> Document:
    return Document(
        url=_text(doc_el, "url", ""),
        domain=_text(doc_el, "domain", ""),
        title=_extract_highlighted_text(doc_el.find("title")),
        headline=_text(doc_el, "headline", None),
        modified_time=_text(doc_el, "modtime", None),
        size=_int_or_none(_text(doc_el, "size", None)),
        charset=_text(doc_el, "charset", None),
        passages=_parse_passages(doc_el.find("passages")),
        language=_prop(doc_el, "lang"),
        mime_type=_prop(doc_el, "mime-type"),
        saved_copy_url=_text(doc_el, "saved-copy-url", None),
        doc_id=doc_el.get("id"),
    )


def _parse_image_document(doc_el: etree._Element) -> ImageDocument:
    return ImageDocument(
        url=_text(doc_el, "url", ""),
        domain=_text(doc_el, "domain", ""),
        title=_extract_highlighted_text(doc_el.find("title")),
        image_url=_text(doc_el, "image-link", None),
        thumbnail_url=_text(doc_el, "thmb-href", None),
        width=_int_or_none(_text(doc_el, "thmb-w", None)),
        height=_int_or_none(_text(doc_el, "thmb-h", None)),
        size=_int_or_none(_text(doc_el, "size", None)),
        mime_type=_prop(doc_el, "mime-type"),
        doc_id=doc_el.get("id"),
    )


def _parse_passages(passages_el: etree._Element | None) -> list[Passage]:
    if passages_el is None:
        return []
    result: list[Passage] = []
    for p_el in passages_el.findall("passage"):
        highlighted = _extract_highlighted_text(p_el)
        plain = highlighted.replace("**", "")
        result.append(Passage(text=plain, highlighted_text=highlighted))
    return result


def _extract_highlighted_text(el: etree._Element | None) -> str:
    if el is None:
        return ""
    parts: list[str] = []
    if el.text:
        parts.append(el.text)
    for child in el:
        if child.tag == "hlword":
            parts.append(f"**{child.text or ''}**")
        else:
            parts.append(child.text or "")
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def _text(parent: etree._Element | None, tag: str, default: str | None) -> str | None:
    if parent is None:
        return default
    el = parent.find(tag)
    if el is not None and el.text:
        return el.text
    return default


def _prop(doc_el: etree._Element, prop_name: str) -> str | None:
    props = doc_el.find("properties")
    if props is None:
        return None
    for child in props:
        if child.tag == prop_name:
            return child.text
    return None


def _int_or_none(val: str | None) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except ValueError:
        return None

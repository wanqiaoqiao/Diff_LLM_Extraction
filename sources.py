from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path

from .models import CandidateArticle

PLURIPOTENT_TERMS = [
    "ipsc", "hipsc", "induced pluripotent", "pluripotent stem cell", "hpsc", "hesc", "esc"
]
PROTOCOL_TERMS = [
    "differentiat", "protocol", "day 0", "day 1", "basal medium", "factor", "marker", "methods"
]


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def strip_html(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(unescape(text))


def extract_xml_text(raw_text: str) -> tuple[str, str]:
    try:
        root = ET.fromstring(raw_text)
    except ET.ParseError:
        return "", strip_html(raw_text)
    title = ""
    for tag in ["article-title", "title", "subject"]:
        elem = root.find(f".//{tag}")
        if elem is not None:
            title = normalize_whitespace(" ".join(elem.itertext()))
            break
    body = normalize_whitespace(" ".join(root.itertext()))
    return title, body


def read_local_file(path: Path) -> tuple[str, str]:
    raw_text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in {".xml", ".nxml"}:
        return extract_xml_text(raw_text)
    if path.suffix.lower() in {".html", ".htm"}:
        return "", strip_html(raw_text)
    return "", normalize_whitespace(raw_text)


def fetch_url_text(url: str) -> tuple[str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "ipsc-llm-doe/0.1"}, method="GET")
    with urllib.request.urlopen(request, timeout=60) as response:
        raw_bytes = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    raw_text = raw_bytes.decode(charset, errors="replace")
    if raw_text.lstrip().startswith("<?xml"):
        return extract_xml_text(raw_text)
    return "", strip_html(raw_text)


def academic_score(text: str, target_cell_type: str) -> float:
    lowered = text.lower()
    target = target_cell_type.lower().strip()
    score = lowered.count(target) * 6.0
    score += sum(lowered.count(term) for term in PLURIPOTENT_TERMS) * 2.0
    score += sum(lowered.count(term) for term in PROTOCOL_TERMS) * 1.0
    if target and target in lowered and any(term in lowered for term in PLURIPOTENT_TERMS):
        score += 8.0
    return score


def expand_sources(sources: list[str], target_cell_type: str, max_candidate_files: int) -> list[CandidateArticle]:
    candidates: list[CandidateArticle] = []
    for source in sources:
        value = source.strip()
        if not value:
            continue
        if value.startswith("http://") or value.startswith("https://"):
            title, text = fetch_url_text(value)
            candidates.append(CandidateArticle(source=value, resolved_source=value, kind="url", text=text, title=title, academic_score=academic_score(text[:120000], target_cell_type)))
            continue
        path = Path(value).expanduser()
        if path.is_file():
            title, text = read_local_file(path)
            candidates.append(CandidateArticle(source=value, resolved_source=str(path), kind="local_file", text=text, title=title, academic_score=academic_score(text[:120000], target_cell_type)))
            continue
        if path.is_dir():
            files: list[Path] = []
            for pattern in ("PMC*.xml", "PMC*.nxml", "PMC*.html", "PMC*.txt", "*.xml", "*.txt"):
                files.extend(sorted(path.glob(pattern)))
            seen: set[str] = set()
            for file_path in files:
                if len(candidates) >= max_candidate_files:
                    break
                key = str(file_path)
                if key in seen:
                    continue
                seen.add(key)
                title, text = read_local_file(file_path)
                if not text:
                    continue
                pmcid_match = re.search(r"PMC\d+", file_path.name, flags=re.I)
                candidates.append(
                    CandidateArticle(
                        source=value,
                        resolved_source=str(file_path),
                        kind="local_file",
                        text=text,
                        title=title,
                        pmcid=pmcid_match.group(0).upper() if pmcid_match else None,
                        academic_score=academic_score(text[:120000], target_cell_type),
                    )
                )
    return candidates

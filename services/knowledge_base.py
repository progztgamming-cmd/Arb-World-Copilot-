import re
from pathlib import Path

from config import SYSTEM_DOCS_PATH


WORD_RE = re.compile(r"[A-Za-z0-9\u0600-\u06FF]+")


def load_docs() -> str:
    if SYSTEM_DOCS_PATH.exists():
        return SYSTEM_DOCS_PATH.read_text(encoding="utf-8", errors="ignore").strip()
    return ""


def detect_language(text: str) -> str:
    return "ar" if re.search(r"[\u0600-\u06FF]", text or "") else "en"


def tokenize(text: str) -> set[str]:
    return {token.lower() for token in WORD_RE.findall(text or "")}


def split_sections(text: str) -> list[str]:
    sections = [block.strip() for block in re.split(r"\n\s*\n", text or "") if block.strip()]
    return sections


def select_relevant_sections(query: str, docs: str, limit: int = 6) -> list[str]:
    query_tokens = tokenize(query)
    scored: list[tuple[int, str]] = []

    for section in split_sections(docs):
        section_tokens = tokenize(section)
        score = len(query_tokens & section_tokens)
        if score > 0:
            scored.append((score, section))

    scored.sort(key=lambda item: (-item[0], -len(item[1])))
    return [section for _, section in scored[:limit]]


def build_knowledge_context(query: str) -> str:
    docs = load_docs()
    if not docs:
        return ""

    relevant = select_relevant_sections(query, docs)
    if relevant:
        return "\n\n---\n\n".join(relevant)

    return docs[:6000]

import csv
import json
import logging
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("ai_coding.leetcode_catalog")

DEFAULT_LEETCODE_CATALOG_PATH = Path("data/leetcode_catalog.json")


class LeetCodeCatalogItem(BaseModel):
    title: str
    slug: str
    url: str
    difficulty: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    description: str = ""


def _slug_to_title(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.strip().split("-") if part)


def normalize_leetcode_record(raw: dict[str, Any]) -> Optional[LeetCodeCatalogItem]:
    slug = str(raw.get("slug") or raw.get("task_id") or "").strip().strip("/")
    title = str(raw.get("title") or "").strip()
    if not title and slug:
        title = _slug_to_title(slug)
    if not slug or not title:
        return None

    url = str(raw.get("url") or f"https://leetcode.com/problems/{slug}/").strip()
    difficulty = str(raw.get("difficulty") or "").strip() or None
    description = str(raw.get("description") or raw.get("problem_description") or "").strip()

    raw_tags = raw.get("tags") or []
    if isinstance(raw_tags, str):
        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
    elif isinstance(raw_tags, list):
        tags = [str(t).strip() for t in raw_tags if str(t).strip()]
    else:
        tags = []

    return LeetCodeCatalogItem(
        title=title,
        slug=slug,
        url=url,
        difficulty=difficulty,
        tags=tags,
        description=description,
    )


def import_leetcode_json(src_path: Path, dest_path: Path = DEFAULT_LEETCODE_CATALOG_PATH) -> list[LeetCodeCatalogItem]:
    with src_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    records = payload if isinstance(payload, list) else payload.get("problems", [])
    return _dedupe_and_save(records, dest_path)


def import_leetcode_csv(src_path: Path, dest_path: Path = DEFAULT_LEETCODE_CATALOG_PATH) -> list[LeetCodeCatalogItem]:
    with src_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        records = list(reader)
    return _dedupe_and_save(records, dest_path)


def _dedupe_and_save(records: list[dict[str, Any]], dest_path: Path) -> list[LeetCodeCatalogItem]:
    items: list[LeetCodeCatalogItem] = []
    seen_urls: set[str] = set()
    for rec in records:
        if not isinstance(rec, dict):
            continue
        item = normalize_leetcode_record(rec)
        if not item or item.url in seen_urls:
            continue
        seen_urls.add(item.url)
        items.append(item)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with dest_path.open("w", encoding="utf-8") as f:
        json.dump([item.model_dump() for item in items], f, indent=2, ensure_ascii=False)
    logger.info("Imported %d verified LeetCode problems into %s", len(items), dest_path)
    return items


def load_leetcode_catalog(path: Path = DEFAULT_LEETCODE_CATALOG_PATH) -> tuple[list[LeetCodeCatalogItem], str]:
    if not path.exists():
        return [], "unavailable (no verified catalogue imported)"
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            return [], "unavailable (invalid catalogue format)"
        items: list[LeetCodeCatalogItem] = []
        seen: set[str] = set()
        for entry in raw:
            if not isinstance(entry, dict):
                continue
            item = normalize_leetcode_record(entry)
            if item and item.url not in seen:
                seen.add(item.url)
                items.append(item)
        if not items:
            return [], "unavailable (imported catalogue is empty)"
        return items, f"imported dataset ({len(items)} problems)"
    except Exception as e:
        logger.warning("Failed to load LeetCode catalog from %s: %s", path, e)
        return [], f"unavailable ({type(e).__name__})"

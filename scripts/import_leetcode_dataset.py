"""
Imports verified LeetCode problem metadata (slug, title, url, difficulty, tags, description)
from the public HuggingFace dataset `newfacade/LeetCodeDataset` into `data/leetcode_catalog.json`.
"""
import sys
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.leetcode_catalog import DEFAULT_LEETCODE_CATALOG_PATH, _dedupe_and_save  # noqa: E402


def fetch_hf_leetcode_rows(total_limit: int = 500) -> list[dict]:
    rows: list[dict] = []
    offset = 0
    batch_size = 100
    while offset < total_limit:
        res = requests.get(
            "https://datasets-server.huggingface.co/rows",
            params={
                "dataset": "newfacade/LeetCodeDataset",
                "config": "default",
                "split": "train",
                "offset": offset,
                "length": min(batch_size, total_limit - offset),
            },
            timeout=15,
        )
        res.raise_for_status()
        payload = res.json()
        batch = payload.get("rows", [])
        if not batch:
            break
        for item in batch:
            row = item.get("row", {})
            if row.get("task_id"):
                rows.append(row)
        offset += len(batch)
    return rows


if __name__ == "__main__":
    raw_rows = fetch_hf_leetcode_rows(total_limit=500)
    saved = _dedupe_and_save(raw_rows, ROOT / DEFAULT_LEETCODE_CATALOG_PATH)
    print(f"Imported {len(saved)} verified LeetCode problems to {DEFAULT_LEETCODE_CATALOG_PATH}")

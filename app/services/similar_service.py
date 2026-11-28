import hashlib
import json
import logging
import math
import re
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional
import requests

from app.schemas.similar import SimilarProblemItem, SimilarProblemsResponse
from app.services.embedding_service import EmbeddingService
from app.services.leetcode_catalog import (
    DEFAULT_LEETCODE_CATALOG_PATH,
    LeetCodeCatalogItem,
    load_leetcode_catalog,
)
from app.services.llm_service import LLMService, safe_json_parse

logger = logging.getLogger("ai_coding.similar")

_CACHE_TTL = 21600.0  # 6 hours for persistent catalog cache
_RESULT_TTL = 600.0   # 10 minutes for query responses
_DISK_CACHE_DIR = Path("data/cache")
_CF_DISK_CACHE = _DISK_CACHE_DIR / "codeforces_catalog.json"
_CC_DISK_CACHE = _DISK_CACHE_DIR / "codechef_search_cache.json"

_CF_CACHE: dict[str, Any] = {"ts": 0.0, "problems": [], "status": "uninitialized"}
_CC_CACHE: dict[str, dict[str, Any]] = {}
_RESULT_CACHE: dict[str, tuple[float, SimilarProblemsResponse]] = {}

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "you", "given",
    "return", "integer", "array", "each", "any", "all", "can", "while", "most",
    "at", "one", "two", "number", "numbers", "problem", "input", "output", "format",
    "constraints", "true", "false", "else", "find", "total", "where",
}


@dataclass
class SimilarityScoringConfig:
    semantic_weight: float = 0.55
    topic_weight: float = 0.25
    algorithm_weight: float = 0.20
    progressive_bonus: float = 5.0
    attempted_bonus: float = 3.0


def clear_similar_caches() -> None:
    _CF_CACHE.update({"ts": 0.0, "problems": [], "status": "uninitialized"})
    _CC_CACHE.clear()
    _RESULT_CACHE.clear()


def _clamp_score(val: Any) -> int:
    try:
        return max(0, min(100, int(round(float(val)))))
    except Exception:
        return 0


def _tokenize(text: str) -> list[str]:
    tokens = [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 1 and t not in _STOPWORDS]
    bigrams = [f"{tokens[i]}_{tokens[i + 1]}" for i in range(len(tokens) - 1)]
    return tokens + bigrams


def cosine_lexical_similarity(text_a: str, text_b: str) -> float:
    """Fallback cosine similarity over token + bigram TF vectors (0.0 to 1.0)."""
    vec_a = Counter(_tokenize(text_a))
    vec_b = Counter(_tokenize(text_b))
    if not vec_a or not vec_b:
        return 0.0
    common = set(vec_a.keys()) & set(vec_b.keys())
    dot = sum(vec_a[k] * vec_b[k] for k in common)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _difficulty_rank(diff: Optional[str]) -> Optional[int]:
    """Maps difficulty strings or numeric ratings to 1 (Easy), 2 (Medium), 3 (Hard)."""
    if not diff:
        return None
    low = diff.strip().lower()
    if low == "easy":
        return 1
    if low == "medium":
        return 2
    if low == "hard":
        return 3
    try:
        num = float(low)
        if num <= 1200:
            return 1
        if num <= 1700:
            return 2
        return 3
    except ValueError:
        return None


def compute_similarity_score(
    problem_text: str,
    extracted_tags: list[str],
    extracted_algorithms: list[str],
    candidate_title: str,
    candidate_tags: list[str],
    semantic_sim: Optional[float] = None,
    config: Optional[SimilarityScoringConfig] = None,
) -> int:
    """
    Combines semantic cosine similarity, topic overlap, and algorithm similarity
    into a configurable 0-100 score.
    """
    cfg = config or SimilarityScoringConfig()
    query_doc = f"{problem_text} {' '.join(extracted_tags)} {' '.join(extracted_algorithms)}"
    cand_doc = f"{candidate_title} {' '.join(candidate_tags)}"

    semantic = semantic_sim if semantic_sim is not None else cosine_lexical_similarity(query_doc, cand_doc)

    q_tags = {t.lower().strip() for t in extracted_tags if t.strip()}
    c_tags = {t.lower().strip() for t in candidate_tags if t.strip()}
    if q_tags and c_tags:
        topic_overlap = len(q_tags & c_tags) / max(1, min(len(q_tags), len(c_tags)))
    else:
        topic_overlap = 0.0

    algo_terms = {a.lower().strip() for a in extracted_algorithms if a.strip()}
    cand_lower = cand_doc.lower()
    algo_hits = sum(1 for a in algo_terms if a in cand_lower)
    algo_sim = (algo_hits / max(1, len(algo_terms))) if algo_terms else 0.0

    raw = (
        semantic * cfg.semantic_weight
        + topic_overlap * cfg.topic_weight
        + algo_sim * cfg.algorithm_weight
    ) * 100.0
    blended = raw + (12.0 if (topic_overlap >= 0.5 and semantic >= 0.25) else 0.0)
    if semantic == 0 and topic_overlap == 0 and algo_sim == 0:
        return 0
    return _clamp_score(max(12, round(blended)))


def _fetch_codeforces_catalog() -> tuple[list[dict[str, Any]], str]:
    now = time.time()
    if _CF_CACHE["problems"] and (now - _CF_CACHE["ts"]) < _CACHE_TTL:
        return _CF_CACHE["problems"], "live (memory cached)"

    # Check persistent disk cache
    if _CF_DISK_CACHE.exists():
        try:
            with _CF_DISK_CACHE.open("r", encoding="utf-8") as f:
                disk = json.load(f)
            if isinstance(disk, dict) and (now - float(disk.get("ts", 0))) < _CACHE_TTL:
                problems = disk.get("problems", [])
                if problems:
                    _CF_CACHE.update({"ts": float(disk["ts"]), "problems": problems, "status": "live (disk cached)"})
                    logger.info("Loaded %d Codeforces problems from disk cache", len(problems))
                    return problems, "live (disk cached)"
        except Exception as e:
            logger.warning("Codeforces disk cache read failed: %s", e)

    t0 = time.time()
    try:
        res = requests.get(
            "https://codeforces.com/api/problemset.problems",
            timeout=6,
            headers={"User-Agent": "AI-Coding-Platform/1.0"},
        )
        if res.status_code == 429:
            logger.warning("Codeforces API rate-limited (HTTP 429)")
            return _CF_CACHE.get("problems", []), "rate_limited (HTTP 429)"
        res.raise_for_status()
        data = res.json()
        if data.get("status") == "OK":
            problems = data.get("result", {}).get("problems", [])
            _CF_CACHE.update({"ts": now, "problems": problems, "status": "live"})
            try:
                _DISK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                with _CF_DISK_CACHE.open("w", encoding="utf-8") as f:
                    json.dump({"ts": now, "problems": problems}, f)
            except Exception as e:
                logger.warning("Codeforces disk cache write failed: %s", e)
            logger.info("Fetched %d Codeforces problems in %.2fs", len(problems), time.time() - t0)
            return problems, "live"
        return _CF_CACHE.get("problems", []), "unavailable (invalid API response)"
    except requests.Timeout:
        logger.warning("Codeforces API timed out")
        return _CF_CACHE.get("problems", []), "unavailable (timeout)"
    except requests.RequestException as e:
        logger.warning("Codeforces API error: %s", e)
        return _CF_CACHE.get("problems", []), f"unavailable ({type(e).__name__})"


def _load_cc_disk_cache() -> None:
    if _CC_CACHE or not _CC_DISK_CACHE.exists():
        return
    try:
        with _CC_DISK_CACHE.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            _CC_CACHE.update(raw)
    except Exception:
        pass


def _save_cc_disk_cache() -> None:
    try:
        _DISK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with _CC_DISK_CACHE.open("w", encoding="utf-8") as f:
            json.dump(_CC_CACHE, f)
    except Exception:
        pass


def _fetch_codechef_search(query: str) -> tuple[list[dict[str, Any]], str]:
    key = query.strip().lower()
    now = time.time()
    _load_cc_disk_cache()
    cached = _CC_CACHE.get(key)
    if cached and (now - float(cached.get("ts", 0))) < _CACHE_TTL:
        return cached.get("problems", []), "live (cached)"
    try:
        res = requests.get(
            "https://www.codechef.com/api/list/problems",
            params={"limit": 25, "search": query},
            timeout=6,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if res.status_code == 429:
            logger.warning("CodeChef API rate-limited (HTTP 429) for query=%s", query)
            return [], "rate_limited (HTTP 429)"
        res.raise_for_status()
        data = res.json()
        if data.get("status") == "success" and isinstance(data.get("data"), list):
            items = data["data"]
            _CC_CACHE[key] = {"ts": now, "problems": items}
            _save_cc_disk_cache()
            return items, "live"
        return [], "unavailable (invalid API response)"
    except requests.Timeout:
        return [], "unavailable (timeout)"
    except requests.RequestException as e:
        return [], f"unavailable ({type(e).__name__})"


class SimilarProblemsService:
    """
    Hybrid recommendation engine combining SentenceTransformer (all-MiniLM-L6-v2)
    embeddings, topic tag overlap, algorithm matching, and user personalization.
    """

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        scoring_config: Optional[SimilarityScoringConfig] = None,
        leetcode_catalog_path: Path = DEFAULT_LEETCODE_CATALOG_PATH,
        fetch_cf_fn: Optional[Callable[[], tuple[list[dict[str, Any]], str]]] = None,
        fetch_cc_fn: Optional[Callable[[str], tuple[list[dict[str, Any]], str]]] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.embedding_service = embedding_service or EmbeddingService()
        self.scoring_config = scoring_config or SimilarityScoringConfig()
        self.leetcode_catalog_path = leetcode_catalog_path
        self._fetch_cf_fn = fetch_cf_fn or _fetch_codeforces_catalog
        self._fetch_cc_fn = fetch_cc_fn or _fetch_codechef_search

    def _extract_problem_profile(self, problem: str, model: str) -> tuple[list[str], list[str], list[str]]:
        prompt = f"""
Analyze this DSA problem and extract search metadata.
Return STRICT JSON ONLY:
{{
  "tags": ["dp", "greedy", "math"],
  "algorithms": ["knapsack", "divisibility", "prefix sum"],
  "keywords": ["budget", "items", "coin"]
}}

PROBLEM:
{problem}
"""
        try:
            response = self.llm_service.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model,
                temperature=0.1,
                max_tokens=1200,
                response_format={"type": "json_object"},
            )
            parsed = safe_json_parse(response.choices[0].message.content)
            if isinstance(parsed, dict):
                tags = [str(t).lower().strip() for t in parsed.get("tags", []) if t][:6]
                algos = [str(a).lower().strip() for a in parsed.get("algorithms", []) if a][:6]
                kws = [str(k).lower().strip() for k in parsed.get("keywords", []) if k][:5]
                if tags or kws:
                    return tags, algos, kws
        except Exception as e:
            logger.debug("LLM profile extraction fallback used: %s", e)

        fallback_tokens = [t for t in _tokenize(problem) if "_" not in t][:6]
        return fallback_tokens[:3], fallback_tokens[:4], fallback_tokens[:3]

    def _infer_target_rank(
        self,
        solved_urls: set[str],
        attempted_urls: set[str],
        target_difficulty: Optional[str],
        all_known_items: list[tuple[str, Optional[str]]],
    ) -> Optional[int]:
        explicit = _difficulty_rank(target_difficulty)
        if explicit is not None:
            return explicit
        solved_ranks = [
            r for url, diff in all_known_items
            if url in solved_urls
            for r in [_difficulty_rank(diff)]
            if r is not None
        ]
        if solved_ranks:
            avg = sum(solved_ranks) / len(solved_ranks)
            return min(3, int(round(avg)) + 1)  # Progressive step up!
        if attempted_urls:
            return 2
        return None

    def _apply_personalization(
        self,
        base_score: int,
        difficulty: Optional[str],
        url: str,
        target_rank: Optional[int],
        attempted_urls: set[str],
    ) -> tuple[int, Optional[str]]:
        bonus = 0.0
        note: Optional[str] = None
        rank = _difficulty_rank(difficulty)
        if target_rank is not None and rank is not None:
            if rank == target_rank:
                bonus += self.scoring_config.progressive_bonus
                note = "Progressive difficulty match for your solved history"
            elif rank == target_rank - 1:
                bonus += 1.0
        if url in attempted_urls:
            bonus += self.scoring_config.attempted_bonus
            note = note or "Previously attempted — good follow-up"
        return _clamp_score(round(base_score + bonus)), note

    def _rank_leetcode(
        self,
        problem: str,
        tags: list[str],
        algorithms: list[str],
        keywords: list[str],
        solved_urls: set[str],
        attempted_urls: set[str],
        exclude_solved: bool,
        target_difficulty: Optional[str],
    ) -> tuple[list[SimilarProblemItem], str]:
        catalog: list[LeetCodeCatalogItem]
        catalog, status = load_leetcode_catalog(self.leetcode_catalog_path)
        if not catalog:
            return [], status

        target_rank = self._infer_target_rank(
            solved_urls,
            attempted_urls,
            target_difficulty,
            [(c.url, c.difficulty) for c in catalog],
        )

        # Compute embeddings for query + catalog (cached persistently in SQLite)
        query_doc = f"{problem}\nTopics: {', '.join(tags)}\nAlgorithms: {', '.join(algorithms)}"
        cand_docs = [
            f"{c.title}\nTopics: {', '.join(c.tags)}\n{c.description[:400]}"
            for c in catalog
        ]
        all_vecs = self.embedding_service.encode_texts([query_doc, *cand_docs])
        query_vec = all_vecs[0]
        cand_vecs = all_vecs[1:]

        scored: list[SimilarProblemItem] = []
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()

        for item, c_vec in zip(catalog, cand_vecs):
            if exclude_solved and item.url in solved_urls:
                continue
            title_key = item.title.lower()
            if item.url in seen_urls or title_key in seen_titles:
                continue

            sem = (
                self.embedding_service.cosine_similarity(query_vec, c_vec)
                if (query_vec is not None and c_vec is not None)
                else None
            )
            base_score = compute_similarity_score(
                problem_text=f"{problem} {' '.join(keywords)}",
                extracted_tags=tags,
                extracted_algorithms=algorithms,
                candidate_title=f"{item.title} {item.description[:250]}",
                candidate_tags=item.tags,
                semantic_sim=sem,
                config=self.scoring_config,
            )
            if base_score < 22:
                continue

            final_score, pers_note = self._apply_personalization(
                base_score, item.difficulty, item.url, target_rank, attempted_urls
            )
            seen_urls.add(item.url)
            seen_titles.add(title_key)

            shared_tags = [t for t in item.tags if t.lower() in set(tags)]
            parts = []
            if sem is not None:
                parts.append(f"Semantic match ({int(round(sem * 100))}%)")
            if shared_tags:
                parts.append(f"shared topics ({', '.join(shared_tags[:3])})")
            if pers_note:
                parts.append(pers_note)
            reason = "; ".join(parts) + "." if parts else "Verified LeetCode match."

            scored.append(
                SimilarProblemItem(
                    title=item.title,
                    platform="leetcode",
                    url=item.url,
                    similarity_score=final_score,
                    difficulty=item.difficulty,
                    tags=item.tags[:4],
                    reason=reason,
                )
            )

        scored.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored[:10], status

    def _rank_codeforces(
        self,
        problem: str,
        tags: list[str],
        algorithms: list[str],
        keywords: list[str],
        solved_urls: set[str],
        attempted_urls: set[str],
        exclude_solved: bool,
        target_difficulty: Optional[str],
    ) -> tuple[list[SimilarProblemItem], str]:
        cf_pool, status = self._fetch_cf_fn()
        if not cf_pool:
            return [], status

        # Fast lexical pre-filter to top 60 candidates, then neural embedding re-rank
        preliminary: list[tuple[int, dict[str, Any], str]] = []
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()

        for p in cf_pool:
            cid = p.get("contestId")
            idx = p.get("index")
            name = str(p.get("name") or "").strip()
            if not (cid and idx and name):
                continue
            url = f"https://codeforces.com/problemset/problem/{cid}/{idx}"
            if exclude_solved and url in solved_urls:
                continue
            title_key = name.lower()
            if url in seen_urls or title_key in seen_titles:
                continue
            p_tags = [str(t) for t in p.get("tags", []) if t]
            lex_score = compute_similarity_score(
                problem_text=f"{problem} {' '.join(keywords)}",
                extracted_tags=tags,
                extracted_algorithms=algorithms,
                candidate_title=name,
                candidate_tags=p_tags,
                config=self.scoring_config,
            )
            if lex_score >= 20:
                seen_urls.add(url)
                seen_titles.add(title_key)
                preliminary.append((lex_score, p, url))

        preliminary.sort(key=lambda x: x[0], reverse=True)
        top_candidates = preliminary[:60]
        if not top_candidates:
            return [], status

        target_rank = self._infer_target_rank(
            solved_urls,
            attempted_urls,
            target_difficulty,
            [(u, str(p["rating"]) if p.get("rating") else None) for _, p, u in top_candidates],
        )

        query_doc = f"{problem}\nTopics: {', '.join(tags)}\nAlgorithms: {', '.join(algorithms)}"
        cand_docs = [f"{p['name']} ({', '.join(p.get('tags', []))})" for _, p, _ in top_candidates]
        all_vecs = self.embedding_service.encode_texts([query_doc, *cand_docs])
        query_vec = all_vecs[0]
        cand_vecs = all_vecs[1:]

        scored: list[SimilarProblemItem] = []
        for (_, p, url), c_vec in zip(top_candidates, cand_vecs):
            name = str(p["name"]).strip()
            p_tags = [str(t) for t in p.get("tags", []) if t]
            diff = str(p["rating"]) if p.get("rating") else None
            sem = (
                self.embedding_service.cosine_similarity(query_vec, c_vec)
                if (query_vec is not None and c_vec is not None)
                else None
            )
            base_score = compute_similarity_score(
                problem_text=f"{problem} {' '.join(keywords)}",
                extracted_tags=tags,
                extracted_algorithms=algorithms,
                candidate_title=name,
                candidate_tags=p_tags,
                semantic_sim=sem,
                config=self.scoring_config,
            )
            final_score, pers_note = self._apply_personalization(
                base_score, diff, url, target_rank, attempted_urls
            )
            shared_tags = [t for t in p_tags if t.lower() in set(tags)]
            parts = []
            if sem is not None:
                parts.append(f"Semantic match ({int(round(sem * 100))}%)")
            if shared_tags:
                parts.append(f"shared topics ({', '.join(shared_tags[:3])})")
            if pers_note:
                parts.append(pers_note)
            reason = "; ".join(parts) + "." if parts else "Related Codeforces problem."

            scored.append(
                SimilarProblemItem(
                    title=name,
                    platform="codeforces",
                    url=url,
                    similarity_score=final_score,
                    difficulty=diff,
                    tags=p_tags[:4],
                    reason=reason,
                )
            )

        scored.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored[:10], status

    def _rank_codechef(
        self,
        problem: str,
        tags: list[str],
        algorithms: list[str],
        keywords: list[str],
        solved_urls: set[str],
        attempted_urls: set[str],
        exclude_solved: bool,
        target_difficulty: Optional[str],
    ) -> tuple[list[SimilarProblemItem], str]:
        search_terms = list(dict.fromkeys([*keywords[:2], *tags[:1]])) or ["array"]
        raw_candidates: list[dict[str, Any]] = []
        last_status = "unavailable"
        for term in search_terms[:3]:
            items, status = self._fetch_cc_fn(term)
            last_status = status
            raw_candidates.extend(items)
            if "rate_limited" in status:
                break

        if not raw_candidates:
            return [], last_status

        deduped: list[tuple[str, str, Optional[str], list[str]]] = []
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        for p in raw_candidates:
            code = str(p.get("code") or "").strip()
            name = str(p.get("name") or "").strip()
            if not code or not name:
                continue
            url = f"https://www.codechef.com/problems/{code}"
            if exclude_solved and url in solved_urls:
                continue
            title_key = name.lower()
            if url in seen_urls or title_key in seen_titles:
                continue
            seen_urls.add(url)
            seen_titles.add(title_key)
            rating = str(p.get("difficulty_rating") or "").strip()
            diff = rating if (rating and rating != "-1") else None
            inferred_tags = [t for t in tags if t in name.lower()] or tags[:2]
            deduped.append((name, url, diff, inferred_tags))

        if not deduped:
            return [], last_status

        target_rank = self._infer_target_rank(
            solved_urls, attempted_urls, target_difficulty, [(u, d) for _, u, d, _ in deduped]
        )

        query_doc = f"{problem}\nTopics: {', '.join(tags)}\nAlgorithms: {', '.join(algorithms)}"
        cand_docs = [f"{name} ({', '.join(tgs)})" for name, _, _, tgs in deduped]
        all_vecs = self.embedding_service.encode_texts([query_doc, *cand_docs])
        query_vec = all_vecs[0]
        cand_vecs = all_vecs[1:]

        scored: list[SimilarProblemItem] = []
        for (name, url, diff, inferred_tags), c_vec in zip(deduped, cand_vecs):
            sem = (
                self.embedding_service.cosine_similarity(query_vec, c_vec)
                if (query_vec is not None and c_vec is not None)
                else None
            )
            base_score = compute_similarity_score(
                problem_text=f"{problem} {' '.join(keywords)}",
                extracted_tags=tags,
                extracted_algorithms=algorithms,
                candidate_title=name,
                candidate_tags=inferred_tags,
                semantic_sim=sem,
                config=self.scoring_config,
            )
            final_score, pers_note = self._apply_personalization(
                base_score, diff, url, target_rank, attempted_urls
            )
            parts = []
            if sem is not None:
                parts.append(f"Semantic match ({int(round(sem * 100))}%)")
            parts.append(f"topics ({', '.join(inferred_tags[:2])})")
            if pers_note:
                parts.append(pers_note)
            scored.append(
                SimilarProblemItem(
                    title=name,
                    platform="codechef",
                    url=url,
                    similarity_score=final_score,
                    difficulty=diff,
                    tags=inferred_tags[:3],
                    reason="; ".join(parts) + ".",
                )
            )

        scored.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored[:10], last_status

    def find_similar(
        self,
        problem: str,
        refresh: bool = False,
        platform: Optional[str] = None,
        solved_urls: Optional[list[str]] = None,
        attempted_urls: Optional[list[str]] = None,
        exclude_solved: bool = False,
        target_difficulty: Optional[str] = None,
        model: Optional[str] = None,
    ) -> SimilarProblemsResponse:
        target_platform = platform.strip().lower() if platform else None
        solved_set = set(solved_urls or [])
        attempted_set = set(attempted_urls or [])
        cache_payload = json.dumps(
            {
                "p": problem.strip(),
                "s": sorted(solved_set),
                "a": sorted(attempted_set),
                "ex": exclude_solved,
                "td": target_difficulty,
                "cat": str(self.leetcode_catalog_path),
            },
            sort_keys=True,
        )
        cache_key = hashlib.sha256(cache_payload.encode("utf-8")).hexdigest()
        now = time.time()
        cached_entry = _RESULT_CACHE.get(cache_key)
        if not refresh and not target_platform and cached_entry:
            ts, cached_res = cached_entry
            if (now - ts) < _RESULT_TTL:
                logger.info("Similar problems cache hit key=%s", cache_key[:10])
                return cached_res

        t0 = time.time()
        target_model = model or self.llm_service.settings.GROQ_MODEL
        tags, algorithms, keywords = self._extract_problem_profile(problem, target_model)

        prev_res = cached_entry[1] if cached_entry else None
        lc_items = prev_res.leetcode if prev_res else []
        lc_status = prev_res.platform_status.get("leetcode", "skipped") if prev_res else "skipped"
        cf_items = prev_res.codeforces if prev_res else []
        cf_status = prev_res.platform_status.get("codeforces", "skipped") if prev_res else "skipped"
        cc_items = prev_res.codechef if prev_res else []
        cc_status = prev_res.platform_status.get("codechef", "skipped") if prev_res else "skipped"

        if target_platform in (None, "leetcode"):
            lc_items, lc_status = self._rank_leetcode(
                problem, tags, algorithms, keywords, solved_set, attempted_set, exclude_solved, target_difficulty
            )
        if target_platform in (None, "codeforces"):
            cf_items, cf_status = self._rank_codeforces(
                problem, tags, algorithms, keywords, solved_set, attempted_set, exclude_solved, target_difficulty
            )
        if target_platform in (None, "codechef"):
            cc_items, cc_status = self._rank_codechef(
                problem, tags, algorithms, keywords, solved_set, attempted_set, exclude_solved, target_difficulty
            )

        logger.info(
            "Similar problems computed in %.2fs (platform=%s, lc=%d [%s], cf=%d [%s], cc=%d [%s])",
            time.time() - t0,
            target_platform or "all",
            len(lc_items), lc_status,
            len(cf_items), cf_status,
            len(cc_items), cc_status,
        )

        response = SimilarProblemsResponse(
            leetcode=lc_items,
            codechef=cc_items,
            codeforces=cf_items,
            platform_status={
                "leetcode": lc_status,
                "codechef": cc_status,
                "codeforces": cf_status,
            },
            model_used=target_model,
        )
        _RESULT_CACHE[cache_key] = (now, response)
        return response

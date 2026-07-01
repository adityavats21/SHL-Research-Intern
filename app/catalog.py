from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "shl_product_catalog.json"

TYPE_CODES = {
    "Ability & Aptitude": "A",
    "Assessment Exercises": "E",
    "Biodata & Situational Judgment": "B",
    "Competencies": "C",
    "Development & 360": "D",
    "Personality & Behavior": "P",
    "Knowledge & Skills": "K",
    "Simulations": "S",
}


def normalize(text: str) -> str:
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> set[str]:
    stop = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "for",
        "in",
        "is",
        "new",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }
    return {t for t in normalize(text).split() if len(t) > 1 and t not in stop}


class Catalog:
    def __init__(self, rows: list[dict[str, Any]]):
        self.items = [self._clean(row) for row in rows if row.get("status") == "ok"]
        self.by_name = {normalize(item["name"]): item for item in self.items}
        self.by_url = {item["url"]: item for item in self.items}

    def _clean(self, row: dict[str, Any]) -> dict[str, Any]:
        keys = row.get("keys") or []
        codes = [TYPE_CODES[k] for k in keys if k in TYPE_CODES]
        return {
            "entity_id": str(row.get("entity_id", "")),
            "name": re.sub(r"\s+", " ", row.get("name", "")).strip(),
            "url": row.get("link", ""),
            "test_type": ",".join(dict.fromkeys(codes)) or "K",
            "keys": keys,
            "description": re.sub(r"\s+", " ", row.get("description", "")).strip(),
            "duration": row.get("duration") or "",
            "languages": row.get("languages") or [],
            "job_levels": row.get("job_levels") or [],
            "remote": row.get("remote") or "",
            "adaptive": row.get("adaptive") or "",
        }

    def get(self, name: str) -> dict[str, Any]:
        key = normalize(name)
        if key not in self.by_name:
            raise KeyError(f"Catalog item not found: {name}")
        return self.by_name[key]

    def rec(self, name: str) -> dict[str, str]:
        item = self.get(name)
        return {"name": item["name"], "url": item["url"], "test_type": item["test_type"]}

    def recommend(self, names: list[str]) -> list[dict[str, str]]:
        seen: set[str] = set()
        out: list[dict[str, str]] = []
        for name in names:
            try:
                rec = self.rec(name)
            except KeyError:
                continue
            if rec["url"] not in seen:
                seen.add(rec["url"])
                out.append(rec)
        return out[:10]

    def search(self, query: str, limit: int = 10) -> list[dict[str, str]]:
        q_tokens = tokenize(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        for item in self.items:
            hay = " ".join(
                [
                    item["name"],
                    item["description"],
                    " ".join(item["keys"]),
                    " ".join(item["job_levels"]),
                    " ".join(item["languages"]),
                ]
            )
            tokens = tokenize(hay)
            overlap = q_tokens & tokens
            if not overlap:
                continue
            score = len(overlap) * 3.0
            nname = normalize(item["name"])
            for phrase in q_tokens:
                if phrase in nname:
                    score += 1.0
            if "Knowledge & Skills" in item["keys"]:
                score += 0.4
            if "Personality & Behavior" in item["keys"] and any(
                w in q_tokens for w in {"personality", "behavior", "behaviour", "fit", "leadership"}
            ):
                score += 1.5
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"name": item["name"], "url": item["url"], "test_type": item["test_type"]}
            for _, item in scored[:limit]
        ]

    def mentioned_items(self, text: str, limit: int = 4) -> list[dict[str, Any]]:
        ntext = normalize(text)
        found: list[dict[str, Any]] = []
        aliases = {
            "opq": "Occupational Personality Questionnaire OPQ32r",
            "opq32r": "Occupational Personality Questionnaire OPQ32r",
            "gsa": "Global Skills Assessment",
            "verify g": "SHL Verify Interactive G+",
            "safety dependability 8 0": "Manufac. & Indust. - Safety & Dependability 8.0",
            "dsi": "Dependability and Safety Instrument (DSI)",
        }
        for alias, name in aliases.items():
            if alias in ntext:
                item = self.get(name)
                if item not in found:
                    found.append(item)
        for item in self.items:
            if normalize(item["name"]) in ntext and item not in found:
                found.append(item)
        return found[:limit]


@lru_cache
def load_catalog() -> Catalog:
    text = CATALOG_PATH.read_text(encoding="utf-8")
    rows = json.loads(text, strict=False)
    return Catalog(rows)

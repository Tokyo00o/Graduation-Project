import csv
import io
import json
from typing import Dict, List, Optional


class SeedRow:
    def __init__(self, content: str, category: str = "general", tags: Optional[List[str]] = None,
                 difficulty: str = "medium", effectiveness: float = 0.0, source: str = ""):
        self.content = content
        self.category = category or "general"
        self.tags = tags or []
        self.difficulty = difficulty or "medium"
        self.effectiveness = effectiveness if effectiveness is not None else 0.0
        self.source = source or ""

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "category": self.category,
            "tags": self.tags,
            "difficulty": self.difficulty,
            "effectiveness": self.effectiveness,
            "source": self.source,
        }


def _normalize(record: dict) -> SeedRow:
    content = (record.get("content") or record.get("prompt") or record.get("seed") or "").strip()
    tags_raw = record.get("tags") or record.get("tag") or []
    if isinstance(tags_raw, str):
        tags = [t.strip() for t in tags_raw.replace(";", ",").split(",") if t.strip()]
    else:
        tags = list(tags_raw) if tags_raw else []
    return SeedRow(
        content=content,
        category=str(record.get("category", "general")),
        tags=tags,
        difficulty=str(record.get("difficulty", "medium")),
        effectiveness=float(record.get("effectiveness", 0) or 0),
        source=str(record.get("source", "")),
    )


def parse_csv(text: str) -> List[SeedRow]:
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        row = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}
        if row.get("content") or row.get("prompt") or row.get("seed"):
            rows.append(_normalize(row))
    return rows


def parse_json(text: str) -> List[SeedRow]:
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("items", data.get("seeds", [data]))
    if not isinstance(data, list):
        raise ValueError("JSON must be an array or object with 'items'/'seeds' key")
    return [_normalize(rec) for rec in data]


def parse_jsonl(text: str) -> List[SeedRow]:
    rows = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        rows.append(_normalize(record))
    return rows


def parse_yaml(text: str) -> List[SeedRow]:
    import yaml
    data = yaml.safe_load(text)
    if isinstance(data, dict):
        data = data.get("items", data.get("seeds", [data]))
    if not isinstance(data, list):
        raise ValueError("YAML must be a list or mapping with 'items'/'seeds' key")
    return [_normalize(rec) for rec in data]


def parse_file(filename: str, content: bytes) -> List[SeedRow]:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    text = content.decode("utf-8-sig")

    parsers = {
        "csv": parse_csv,
        "json": parse_json,
        "jsonl": parse_jsonl,
        "yaml": parse_yaml,
        "yml": parse_yaml,
    }

    parser = parsers.get(ext)
    if not parser:
        raise ValueError(f"Unsupported file format: .{ext} (supported: csv, json, jsonl, yaml)")

    rows = parser(text)
    if not rows:
        raise ValueError("No valid seed entries found in file")
    for r in rows:
        if not r.content:
            raise ValueError("Each seed entry must have a non-empty 'content' field")
    return rows

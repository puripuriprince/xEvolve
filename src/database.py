from __future__ import annotations

import json
import os
import random
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

__all__ = [
    "initialize",
    "load",
    "save",
    "add",
    "sample",
]

_DB_PATH = Path(os.environ.get("DATABASE_FILE", "database.json"))


def _ensure_file() -> None:
    if not _DB_PATH.exists():
        _DB_PATH.write_text("[]")


# Public API ----------------------------------------------------------------

def initialize() -> None:
    """Create the on-disk JSON database if missing."""
    _ensure_file()


def load() -> List[Dict[str, Any]]:
    _ensure_file()
    return json.loads(_DB_PATH.read_text())


def save(db: List[Dict[str, Any]]) -> None:
    _DB_PATH.write_text(json.dumps(db, indent=4))


def add(
    program: str,
    result: Dict[str, Any] | None = None,
    *,
    parent_uuid: str | None = None,
    idea: str = "",
) -> Dict[str, Any]:
    entry = {
        "uuid": str(uuid.uuid4()),
        "idea": idea,
        "program": program,
        "result": result or {},
        "parent_uuid": parent_uuid,
    }
    db = load()
    db.append(entry)
    save(db)
    return entry


def sample(*, inspirations: int = 2) -> Tuple[str, List[str], str | None]:
    """Return a (parent_code, inspiration_codes, parent_uuid) triple."""
    db = load()
    if not db:
        return "", [], None

    parent = random.choice(db)
    pool = [e for e in db if e["uuid"] != parent["uuid"]]
    insp_codes: List[str] = []
    if pool:
        sample_n = min(inspirations, len(pool))
        insp_codes = [e["program"] for e in random.sample(pool, sample_n)]

    return parent["program"], insp_codes, parent["uuid"] 
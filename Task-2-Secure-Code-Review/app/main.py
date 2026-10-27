"""Corrected FastAPI application for the CodeAlpha secure-code lab."""
from __future__ import annotations

import hmac
import logging
import os
import sqlite3
import threading
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.middleware import SecurityHeadersMiddleware
from app.scanner.common import is_excluded_target
from app.scanner.orchestrator import ScanOrchestrator

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


DB_PATH = Path(
    os.environ.get(
        "LAB_DB_PATH",
        PROJECT_ROOT / "data" / "review.sqlite3",
    )
).expanduser()
API_KEY = os.environ.get("LAB_API_KEY", "")
SCAN_ROOT = Path(os.environ.get("LAB_SCAN_ROOT", PROJECT_ROOT)).expanduser().resolve()
ENABLE_DOCS = _env_flag("LAB_ENABLE_DOCS")

# SQLite INTEGER values are signed 64-bit. Reject larger Python integers
# before binding them so a request cannot trigger an OverflowError/500.
SQLITE_MAX_INTEGER = 2**63 - 1

# A single in-process slot prevents concurrent expensive scans from exhausting
# CPU and memory. It is a concurrency guard, not a distributed rate limiter.
_SCAN_SLOT = threading.BoundedSemaphore(1)

app = FastAPI(
    title="CodeAlpha SecureCodeReview",
    version="2.1.0",
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_DOCS else None,
)

app.add_middleware(SecurityHeadersMiddleware)


class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must contain non-whitespace characters")
        if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value):
            raise ValueError("name must not contain control characters")
        return value


class ScanRequest(BaseModel):
    target_path: str = Field(
        default=".",
        min_length=1,
        max_length=256,
        description="Relative path or directory below LAB_SCAN_ROOT to scan.",
    )

    @field_validator("target_path")
    @classmethod
    def validate_target_path(cls, value: str) -> str:
        if any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value):
            raise ValueError("target_path must not contain control characters")
        return value


def get_db():
    db = None
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(DB_PATH, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute(
            "CREATE TABLE IF NOT EXISTS items "
            "(id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
        )
        db.commit()
        yield db
    except sqlite3.Error:
        logger.exception("Database operation failed")
        raise
    except OSError:
        logger.exception("Database directory or file access failed")
        raise
    finally:
        if db is not None:
            db.close()


def require_key(x_api_key: str | None = Header(default=None)) -> str:
    if not API_KEY or not API_KEY.strip() or not x_api_key or len(x_api_key) > 4096:
        raise HTTPException(
            status_code=401, detail="Unauthorized or missing API Key"
        )
    try:
        valid = hmac.compare_digest(
            API_KEY.encode("utf-8"),
            x_api_key.encode("utf-8"),
        )
    except (TypeError, UnicodeEncodeError):
        valid = False
    if not valid:
        raise HTTPException(
            status_code=401, detail="Unauthorized or missing API Key"
        )
    return x_api_key


def _escape_like(value: str) -> str:
    """Escape SQLite LIKE wildcards so search input is treated literally."""
    return value.replace("!", "!!").replace("%", "!%").replace("_", "!_")


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/api/v1/demo", dependencies=[Depends(require_key)])
def read_demo(db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
    )
    tables = [row[0] for row in cursor.fetchall()]
    return {"status": "ok", "tables": tables}


@app.get("/items", dependencies=[Depends(require_key)])
def search_items(
    q: str = Query(default="", max_length=64),
    db: sqlite3.Connection = Depends(get_db),
):
    cursor = db.cursor()
    pattern = f"%{_escape_like(q)}%"
    cursor.execute(
        "SELECT id, name FROM items WHERE name LIKE ? ESCAPE '!' ORDER BY id",
        (pattern,),
    )
    items = [dict(row) for row in cursor.fetchall()]
    return {"items": items}


@app.post("/items", status_code=201, dependencies=[Depends(require_key)])
def create_item(item: Item, db: sqlite3.Connection = Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("INSERT INTO items (name) VALUES (?)", (item.name,))
    db.commit()
    return {"id": cursor.lastrowid, "name": item.name}


@app.get("/items/{item_id}", dependencies=[Depends(require_key)])
def get_item(item_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not 0 < item_id <= SQLITE_MAX_INTEGER:
        raise HTTPException(status_code=400, detail="Invalid ID")
    cursor = db.cursor()
    cursor.execute("SELECT id, name FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return dict(row)


@app.post("/api/v1/scan", dependencies=[Depends(require_key)])
def trigger_security_scan(request: ScanRequest):
    try:
        target_dir = (SCAN_ROOT / request.target_path).resolve()
    except (OSError, RuntimeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid path.") from None

    if not target_dir.is_relative_to(SCAN_ROOT):
        raise HTTPException(status_code=400, detail="Path traversal detected.")
    if is_excluded_target(SCAN_ROOT, target_dir):
        raise HTTPException(
            status_code=400, detail="Target directory is not allowed."
        )
    if not target_dir.is_dir():
        raise HTTPException(
            status_code=400, detail="Target directory does not exist."
        )

    if not _SCAN_SLOT.acquire(blocking=False):
        raise HTTPException(
            status_code=429,
            detail="A scan is already in progress. Retry later.",
        )

    try:
        result = ScanOrchestrator().run_scan(target_dir)
    except Exception:
        logger.exception("Security scan failed unexpectedly")
        raise HTTPException(status_code=500, detail="Scan failed.") from None
    finally:
        _SCAN_SLOT.release()

    error_code = result.get("summary", {}).get("error")
    if result.get("status") == "error":
        if error_code in {
            "invalid_target",
            "excluded_target",
            "target_too_large",
            "target_unreadable",
        }:
            raise HTTPException(status_code=400, detail="Invalid scan target.")
        raise HTTPException(
            status_code=503,
            detail="Security scanners are unavailable.",
        )

    return result

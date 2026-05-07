"""Phase 1: write-only Google Sheet sync for system-owned columns.

User-owned columns (Status, Last Touch, Next Touch, Notes) are appended to the
header but never overwritten by Phase 1. Bidirectional sync arrives in Phase 2.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any, Optional

from src.config import get_settings
from src.utils.logging import get_logger

log = get_logger(__name__)


SYSTEM_COLUMNS: list[str] = [
    "Prospect ID",
    "Name",
    "Title",
    "Org",
    "Email",
    "Email Confidence",
    "LinkedIn",
    "Twitter",
    "Categories",
    "Tier",
    "Composite",
    "Services Fit",
    "AI Literacy",
    "Operator Depth",
    "Check Size Fit",
    "Warm Access",
    "Rationale",
    "Warm Paths",
    "Source",
    "Date Added",
    "Date Updated",
]

USER_COLUMNS: list[str] = [
    "Status",
    "Last Touch",
    "Next Touch",
    "Notes",
]

ALL_COLUMNS: list[str] = SYSTEM_COLUMNS + USER_COLUMNS


def _fmt_dt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return str(value)


def _build_rows(conn: sqlite3.Connection) -> list[list[str]]:
    sql = """
    SELECT
        p.id, p.display_name, p.title, p.primary_org,
        p.email, p.email_confidence, p.linkedin_url, p.twitter_handle,
        p.candidate_categories, p.created_at, p.updated_at,
        c.tier, c.composite_score,
        c.services_thesis_fit, c.ai_literacy, c.operator_depth,
        c.check_size_fit, c.warm_intro_accessibility, c.rationale,
        (
            SELECT GROUP_CONCAT(source, ', ') FROM (
                SELECT DISTINCT source FROM source_records WHERE prospect_id = p.id
            )
        ) AS sources,
        (
            SELECT GROUP_CONCAT(path_type || ':' || path_detail, '; ')
            FROM warm_paths WHERE prospect_id = p.id
        ) AS warm_paths
    FROM prospects p
    LEFT JOIN latest_classifications c ON c.prospect_id = p.id
    WHERE COALESCE(c.tier, '2') != 'drop'
    ORDER BY p.id
    """
    rows: list[list[str]] = []
    for r in conn.execute(sql):
        cats = json.loads(r["candidate_categories"] or "[]")
        rows.append([
            str(r["id"]),
            r["display_name"] or "",
            r["title"] or "",
            r["primary_org"] or "",
            r["email"] or "",
            f"{r['email_confidence']:.2f}" if r["email_confidence"] is not None else "",
            r["linkedin_url"] or "",
            r["twitter_handle"] or "",
            ", ".join(cats),
            r["tier"] or "",
            str(r["composite_score"]) if r["composite_score"] is not None else "",
            str(r["services_thesis_fit"]) if r["services_thesis_fit"] is not None else "",
            str(r["ai_literacy"]) if r["ai_literacy"] is not None else "",
            str(r["operator_depth"]) if r["operator_depth"] is not None else "",
            str(r["check_size_fit"]) if r["check_size_fit"] is not None else "",
            str(r["warm_intro_accessibility"]) if r["warm_intro_accessibility"] is not None else "",
            r["rationale"] or "",
            r["warm_paths"] or "",
            r["sources"] or "",
            _fmt_dt(r["created_at"]),
            _fmt_dt(r["updated_at"]),
        ])
    return rows


def sync(conn: sqlite3.Connection, sheet_id: Optional[str] = None) -> int:
    """Push system-owned columns to the configured Google Sheet.

    Returns the number of data rows written. The sheet's first tab is replaced.
    User-owned columns are appended to the header but values are NOT touched
    (Phase 1 contract).
    """
    settings = get_settings()
    sheet_id = sheet_id or settings.google_sheet_id
    if not sheet_id:
        raise RuntimeError("GOOGLE_SHEET_ID not configured")

    sa_path = settings.google_service_account_json_path
    if not sa_path.exists():
        raise RuntimeError(
            f"Google service account JSON not found at {sa_path}. "
            "Set GOOGLE_SERVICE_ACCOUNT_JSON_PATH in .env."
        )

    import gspread
    from google.oauth2.service_account import Credentials

    rows = _build_rows(conn)
    log.info("sheet.sync.start", row_count=len(rows), sheet_id=sheet_id)

    creds = Credentials.from_service_account_file(
        str(sa_path),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.sheet1

    existing_header = worksheet.row_values(1) if worksheet.row_count >= 1 else []
    if existing_header != ALL_COLUMNS:
        worksheet.update("A1", [ALL_COLUMNS])

    if rows:
        last_col_letter = _col_letter(len(SYSTEM_COLUMNS))
        worksheet.update(f"A2:{last_col_letter}{1 + len(rows)}", rows)

    log.info("sheet.sync.done", rows_written=len(rows))
    return len(rows)


def _col_letter(n: int) -> str:
    """1 -> A, 26 -> Z, 27 -> AA, ..."""
    out = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        out = chr(ord("A") + rem) + out
    return out

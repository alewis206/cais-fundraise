import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from src.config import get_settings
from src.models import Prospect, RawProspect
from src.utils.logging import get_logger
from src.utils.names import canonicalize, org_key

log = get_logger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@contextmanager
def connect(db_path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    path = Path(db_path) if db_path else settings.db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TIMESTAMP NOT NULL
        )
        """
    )


def run_migrations(db_path: Optional[Path] = None) -> list[str]:
    """Apply any unapplied .sql files in src/migrations/ in lexical order."""
    settings = get_settings()
    migrations_dir = settings.migrations_dir
    applied: list[str] = []

    with connect(db_path) as conn:
        _ensure_migrations_table(conn)
        existing = {
            row["filename"]
            for row in conn.execute("SELECT filename FROM schema_migrations")
        }
        for sql_file in sorted(migrations_dir.glob("*.sql")):
            if sql_file.name in existing:
                continue
            log.info("migration.apply", filename=sql_file.name)
            conn.executescript(sql_file.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO schema_migrations(filename, applied_at) VALUES (?, ?)",
                (sql_file.name, _utcnow()),
            )
            applied.append(sql_file.name)
    return applied


def _row_to_prospect(row: sqlite3.Row) -> Prospect:
    return Prospect(
        id=row["id"],
        canonical_name=row["canonical_name"],
        display_name=row["display_name"],
        primary_org=row["primary_org"],
        title=row["title"],
        email=row["email"],
        email_confidence=row["email_confidence"],
        linkedin_url=row["linkedin_url"],
        twitter_handle=row["twitter_handle"],
        crunchbase_url=row["crunchbase_url"],
        bio=row["bio"],
        candidate_categories=json.loads(row["candidate_categories"] or "[]"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _find_existing(
    conn: sqlite3.Connection, raw: RawProspect, canonical: str
) -> Optional[sqlite3.Row]:
    """Match by (canonical_name, primary_org), then linkedin_url, then email."""
    org = org_key(raw.primary_org)
    row = conn.execute(
        """
        SELECT * FROM prospects
        WHERE canonical_name = ?
          AND COALESCE(LOWER(primary_org), '') = ?
        LIMIT 1
        """,
        (canonical, org),
    ).fetchone()
    if row:
        return row

    if raw.linkedin_url:
        row = conn.execute(
            "SELECT * FROM prospects WHERE linkedin_url = ? LIMIT 1",
            (raw.linkedin_url,),
        ).fetchone()
        if row:
            return row

    if raw.email:
        row = conn.execute(
            "SELECT * FROM prospects WHERE email = ? LIMIT 1",
            (raw.email,),
        ).fetchone()
        if row:
            return row

    return None


def _merge_categories(existing_json: Optional[str], new: list[str]) -> str:
    cur = json.loads(existing_json or "[]")
    for c in new:
        if c and c not in cur:
            cur.append(c)
    return json.dumps(cur)


def upsert_prospect(conn: sqlite3.Connection, raw: RawProspect) -> tuple[int, bool]:
    """Insert or merge a RawProspect. Returns (prospect_id, created).

    On collision, only fills null fields — never overwrites existing values.
    Always appends a `source_records` row.
    """
    canonical = canonicalize(raw.full_name)
    if not canonical:
        raise ValueError("Cannot ingest prospect with empty canonical name")

    now = _utcnow()
    existing = _find_existing(conn, raw, canonical)

    if existing is None:
        cur = conn.execute(
            """
            INSERT INTO prospects (
                canonical_name, display_name, primary_org, title,
                email, linkedin_url, twitter_handle, crunchbase_url, bio,
                candidate_categories, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                canonical,
                raw.full_name.strip(),
                raw.primary_org,
                raw.title,
                raw.email,
                raw.linkedin_url,
                raw.twitter_handle,
                raw.crunchbase_url,
                raw.bio,
                json.dumps(raw.candidate_categories),
                now,
                now,
            ),
        )
        prospect_id = int(cur.lastrowid)
        created = True
    else:
        prospect_id = int(existing["id"])
        merged_categories = _merge_categories(
            existing["candidate_categories"], raw.candidate_categories
        )
        conn.execute(
            """
            UPDATE prospects SET
                primary_org = COALESCE(primary_org, ?),
                title = COALESCE(title, ?),
                email = COALESCE(email, ?),
                linkedin_url = COALESCE(linkedin_url, ?),
                twitter_handle = COALESCE(twitter_handle, ?),
                crunchbase_url = COALESCE(crunchbase_url, ?),
                bio = COALESCE(bio, ?),
                candidate_categories = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                raw.primary_org,
                raw.title,
                raw.email,
                raw.linkedin_url,
                raw.twitter_handle,
                raw.crunchbase_url,
                raw.bio,
                merged_categories,
                now,
                prospect_id,
            ),
        )
        created = False

    conn.execute(
        """
        INSERT INTO source_records (prospect_id, source, source_context_json, fetched_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            prospect_id,
            raw.source,
            json.dumps(raw.source_context),
            now,
        ),
    )

    return prospect_id, created


def list_prospects(conn: sqlite3.Connection) -> list[Prospect]:
    rows = conn.execute("SELECT * FROM prospects ORDER BY id").fetchall()
    return [_row_to_prospect(r) for r in rows]


def list_prospects_needing_classification(conn: sqlite3.Connection) -> list[Prospect]:
    rows = conn.execute(
        """
        SELECT p.* FROM prospects p
        LEFT JOIN latest_classifications c ON c.prospect_id = p.id
        WHERE c.id IS NULL
        ORDER BY p.id
        """
    ).fetchall()
    return [_row_to_prospect(r) for r in rows]


def insert_classification(
    conn: sqlite3.Connection,
    prospect_id: int,
    output,
    model_used: str,
    prompt_version: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO classifications (
            prospect_id, services_thesis_fit, ai_literacy, operator_depth,
            check_size_fit, warm_intro_accessibility, composite_score, tier,
            rationale, flags_json, confidence, model_used, prompt_version, classified_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prospect_id,
            output.services_thesis_fit,
            output.ai_literacy,
            output.operator_depth,
            output.check_size_fit,
            output.warm_intro_accessibility,
            output.composite_score,
            output.tier,
            output.rationale,
            json.dumps(output.flags),
            output.confidence,
            model_used,
            prompt_version,
            _utcnow(),
        ),
    )
    return int(cur.lastrowid)

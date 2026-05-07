import csv
from pathlib import Path
from typing import Iterator, Optional

import yaml

from src.config import get_settings
from src.models import RawProspect
from src.utils.logging import get_logger

log = get_logger(__name__)


DEFAULT_COLUMN_MAPPING: dict[str, list[str]] = {
    "name": ["name", "Full Name", "Name"],
    "org": ["org", "Company", "Organization"],
    "role": ["role", "Title", "Position"],
    "linkedin_url": ["linkedin_url", "LinkedIn URL", "LinkedIn"],
    "twitter_handle": ["twitter_handle", "Twitter", "X Handle"],
    "email": ["email", "Email"],
    "categories": ["categories"],
    "source_note": ["source_note", "Notes"],
}


def _load_source_config(name: str) -> Optional[dict]:
    settings = get_settings()
    path = settings.sources_config_path
    if not path.exists():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for entry in data.get("sources", []) or []:
        if entry.get("name") == name:
            return entry
    return None


def _pick(row: dict[str, str], candidates: list[str]) -> Optional[str]:
    norm_row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
    for c in candidates:
        v = norm_row.get(c.strip().lower())
        if v:
            return v
    return None


def _split_categories(value: Optional[str], extra: list[str]) -> list[str]:
    cats = list(extra)
    if value:
        for c in value.split(","):
            c = c.strip()
            if c and c not in cats:
                cats.append(c)
    return cats


def _expand_paths(paths: list[str]) -> list[Path]:
    """Expand the configured paths into a list of CSV files.

    Directories are expanded to every *.csv they contain (non-recursive).
    """
    settings = get_settings()
    out: list[Path] = []
    for raw in paths:
        p = Path(raw)
        if not p.is_absolute():
            p = settings.repo_root / p
        if p.is_dir():
            out.extend(sorted(p.glob("*.csv")))
        elif p.exists():
            out.append(p)
        else:
            log.warning("manual_csv.path_missing", path=str(p))
    return out


class ManualCSVAdapter:
    name = "manual_csv"

    def __init__(
        self,
        paths: Optional[list[str]] = None,
        column_mapping: Optional[dict[str, list[str]]] = None,
        extra_categories: Optional[list[str]] = None,
    ):
        cfg = _load_source_config(self.name) or {}
        self.paths = paths if paths is not None else cfg.get("paths", [])
        merged = dict(DEFAULT_COLUMN_MAPPING)
        for k, v in (column_mapping or cfg.get("column_mapping") or {}).items():
            merged[k] = v
        self.column_mapping = merged
        self.extra_categories = extra_categories or []

    def fetch(self, **kwargs) -> Iterator[RawProspect]:
        files = _expand_paths(self.paths)
        if not files:
            log.warning("manual_csv.no_files", configured_paths=self.paths)
            return

        for csv_path in files:
            file_categories = list(self.extra_categories)
            yield from self._read_file(csv_path, file_categories)

    def _read_file(self, csv_path: Path, file_categories: list[str]) -> Iterator[RawProspect]:
        log.info("manual_csv.read", path=str(csv_path))
        with csv_path.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            for i, row in enumerate(reader, start=2):  # row 1 is header
                name = _pick(row, self.column_mapping["name"])
                if not name:
                    log.debug("manual_csv.skip_no_name", file=csv_path.name, line=i)
                    continue

                cats = _split_categories(
                    _pick(row, self.column_mapping["categories"]),
                    file_categories,
                )

                yield RawProspect(
                    full_name=name,
                    primary_org=_pick(row, self.column_mapping["org"]),
                    title=_pick(row, self.column_mapping["role"]),
                    linkedin_url=_pick(row, self.column_mapping["linkedin_url"]),
                    twitter_handle=_pick(row, self.column_mapping["twitter_handle"]),
                    email=_pick(row, self.column_mapping["email"]),
                    source=self.name,
                    source_context={
                        "file": csv_path.name,
                        "line": i,
                        "source_note": _pick(row, self.column_mapping["source_note"]),
                    },
                    candidate_categories=cats,
                )

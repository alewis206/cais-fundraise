import csv
import importlib
from pathlib import Path

import pytest


@pytest.fixture
def csv_dir(tmp_path):
    return tmp_path / "seeds"


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def test_reads_basic_csv_with_canonical_columns(csv_dir, monkeypatch):
    f = csv_dir / "initial.csv"
    _write_csv(
        f,
        ["name", "org", "role", "linkedin_url", "email", "categories"],
        [
            [
                "Ada Lovelace",
                "Analytical Engines",
                "Founder",
                "https://linkedin.com/in/ada",
                "ada@ae.com",
                "operator_angel,rpa_alumni",
            ],
            [
                "Justin Welsh",
                "The Saturday Solopreneur",
                "Operator",
                "https://linkedin.com/in/justinwelsh",
                "",
                "audience_founder",
            ],
        ],
    )

    import src.sources.manual_csv as mod

    importlib.reload(mod)
    adapter = mod.ManualCSVAdapter(paths=[str(f)])
    out = list(adapter.fetch())

    assert len(out) == 2
    ada = out[0]
    assert ada.full_name == "Ada Lovelace"
    assert ada.primary_org == "Analytical Engines"
    assert ada.email == "ada@ae.com"
    assert "operator_angel" in ada.candidate_categories
    assert "rpa_alumni" in ada.candidate_categories
    assert ada.source == "manual_csv"


def test_accepts_alternate_column_headers(csv_dir):
    f = csv_dir / "linkedin.csv"
    _write_csv(
        f,
        ["Full Name", "Company", "Title", "LinkedIn URL"],
        [["Daniel Dines", "UiPath", "Founder", "https://linkedin.com/in/dines"]],
    )

    import src.sources.manual_csv as mod

    adapter = mod.ManualCSVAdapter(paths=[str(f)])
    out = list(adapter.fetch())
    assert len(out) == 1
    assert out[0].full_name == "Daniel Dines"
    assert out[0].primary_org == "UiPath"


def test_ingests_every_csv_in_a_directory(csv_dir):
    _write_csv(csv_dir / "a.csv", ["name"], [["Ada Lovelace"]])
    _write_csv(csv_dir / "b.csv", ["name"], [["Grace Hopper"]])

    import src.sources.manual_csv as mod

    adapter = mod.ManualCSVAdapter(paths=[str(csv_dir)])
    names = sorted(p.full_name for p in adapter.fetch())
    assert names == ["Ada Lovelace", "Grace Hopper"]


def test_skips_rows_with_no_name(csv_dir):
    f = csv_dir / "skips.csv"
    _write_csv(f, ["name", "org"], [["", "X"], ["Ada", "Y"]])

    import src.sources.manual_csv as mod

    adapter = mod.ManualCSVAdapter(paths=[str(f)])
    out = list(adapter.fetch())
    assert [p.full_name for p in out] == ["Ada"]


def test_missing_path_does_not_crash(csv_dir):
    import src.sources.manual_csv as mod

    adapter = mod.ManualCSVAdapter(paths=[str(csv_dir / "does-not-exist.csv")])
    assert list(adapter.fetch()) == []

"""Phase 1 acceptance: ingest -> classify -> dedupe-on-rerun."""

import csv

from src import classifier as classifier_mod
from src import db
from src.sources.manual_csv import ManualCSVAdapter


def _write_seed(path, n: int = 100) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "org", "role", "linkedin_url", "source_note"])
        for i in range(n):
            w.writerow([
                f"Person {i}",
                f"Org {i % 10}",
                "Operator",
                f"https://linkedin.com/in/person{i}",
                "from initial seed",
            ])


def test_phase1_acceptance(tmp_db, tmp_path):
    seed = tmp_path / "seeds" / "initial.csv"
    _write_seed(seed, 100)
    adapter = ManualCSVAdapter(paths=[str(seed)])

    with db.connect(tmp_db) as conn:
        for raw in adapter.fetch():
            db.upsert_prospect(conn, raw)
        prospects = db.list_prospects(conn)
        assert len(prospects) == 100

        # Classify everything with the stub.
        version = classifier_mod.prompt_version()
        for p in prospects:
            output = classifier_mod.classify(p)
            db.insert_classification(
                conn,
                prospect_id=p.id,
                output=output,
                model_used=classifier_mod.STUB_MODEL_NAME,
                prompt_version=version,
            )

        tier_counts = dict(
            conn.execute(
                "SELECT tier, COUNT(*) FROM latest_classifications GROUP BY tier"
            ).fetchall()
        )
        assert tier_counts == {"2": 100}

    # Re-running ingestion does not duplicate rows.
    with db.connect(tmp_db) as conn:
        for raw in adapter.fetch():
            db.upsert_prospect(conn, raw)
        assert len(db.list_prospects(conn)) == 100

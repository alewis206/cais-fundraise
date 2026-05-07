from src import db
from src.models import RawProspect


def _raw(**overrides):
    base = dict(
        full_name="Ada Lovelace",
        primary_org="Analytical Engines Inc",
        title="Founder",
        source="manual_csv",
        candidate_categories=["operator_angel"],
    )
    base.update(overrides)
    return RawProspect(**base)


def test_insert_then_reinsert_does_not_duplicate(tmp_db):
    with db.connect(tmp_db) as conn:
        pid1, created1 = db.upsert_prospect(conn, _raw())
        pid2, created2 = db.upsert_prospect(conn, _raw())

    assert pid1 == pid2
    assert created1 is True
    assert created2 is False


def test_dedupe_strips_accents_and_case(tmp_db):
    with db.connect(tmp_db) as conn:
        pid1, _ = db.upsert_prospect(
            conn, _raw(full_name="María García", primary_org="Acme")
        )
        pid2, created = db.upsert_prospect(
            conn, _raw(full_name="MARIA GARCIA", primary_org="Acme")
        )

    assert pid1 == pid2
    assert created is False


def test_merge_fills_null_fields_and_appends_categories(tmp_db):
    with db.connect(tmp_db) as conn:
        pid, _ = db.upsert_prospect(
            conn,
            _raw(email=None, candidate_categories=["operator_angel"]),
        )
        db.upsert_prospect(
            conn,
            _raw(email="ada@example.com", candidate_categories=["rpa_alumni"]),
        )

        row = conn.execute(
            "SELECT email, candidate_categories FROM prospects WHERE id = ?", (pid,)
        ).fetchone()

    assert row["email"] == "ada@example.com"
    import json

    assert set(json.loads(row["candidate_categories"])) == {"operator_angel", "rpa_alumni"}


def test_existing_value_is_never_overwritten(tmp_db):
    with db.connect(tmp_db) as conn:
        pid, _ = db.upsert_prospect(conn, _raw(email="first@example.com"))
        db.upsert_prospect(conn, _raw(email="second@example.com"))
        row = conn.execute(
            "SELECT email FROM prospects WHERE id = ?", (pid,)
        ).fetchone()
    assert row["email"] == "first@example.com"


def test_match_by_linkedin_url_when_org_differs(tmp_db):
    with db.connect(tmp_db) as conn:
        pid1, _ = db.upsert_prospect(
            conn,
            _raw(
                full_name="Daniel Dines",
                primary_org="UiPath",
                linkedin_url="https://www.linkedin.com/in/danieldines",
            ),
        )
        pid2, created = db.upsert_prospect(
            conn,
            _raw(
                full_name="Daniel Dines",
                primary_org=None,
                linkedin_url="https://www.linkedin.com/in/danieldines",
            ),
        )
    assert pid1 == pid2
    assert created is False


def test_each_ingest_appends_a_source_record(tmp_db):
    with db.connect(tmp_db) as conn:
        pid, _ = db.upsert_prospect(conn, _raw())
        db.upsert_prospect(conn, _raw())
        n = conn.execute(
            "SELECT COUNT(*) FROM source_records WHERE prospect_id = ?", (pid,)
        ).fetchone()[0]
    assert n == 2

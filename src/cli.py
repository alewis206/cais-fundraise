from typing import Optional

import typer

from src import classifier as classifier_mod
from src import db
from src.config import get_settings
from src.sources.manual_csv import ManualCSVAdapter
from src.utils.logging import configure_logging, get_logger

app = typer.Typer(add_completion=False, help="CAIS prospects pipeline.")
log = get_logger(__name__)


SOURCE_REGISTRY = {
    "manual_csv": ManualCSVAdapter,
}


@app.callback()
def _bootstrap() -> None:
    configure_logging()


@app.command()
def migrate() -> None:
    """Apply any pending SQL migrations."""
    applied = db.run_migrations()
    if applied:
        typer.echo(f"applied: {', '.join(applied)}")
    else:
        typer.echo("no migrations to apply")


@app.command()
def ingest(
    source: str = typer.Argument(..., help="Source adapter name, e.g. manual_csv."),
) -> None:
    """Ingest prospects from a configured source adapter."""
    db.run_migrations()

    adapter_cls = SOURCE_REGISTRY.get(source)
    if not adapter_cls:
        raise typer.BadParameter(
            f"unknown source '{source}'. known: {sorted(SOURCE_REGISTRY)}"
        )
    adapter = adapter_cls()

    created = 0
    merged = 0
    with db.connect() as conn:
        for raw in adapter.fetch():
            _, was_created = db.upsert_prospect(conn, raw)
            if was_created:
                created += 1
            else:
                merged += 1

    log.info("ingest.done", source=source, created=created, merged=merged)
    typer.echo(f"{source}: created={created} merged={merged}")


@app.command()
def classify(
    prospect_id: Optional[int] = typer.Option(None, "--prospect-id"),
    all_: bool = typer.Option(False, "--all"),
) -> None:
    """Classify prospects. Phase 1 uses a stub; cost is zero."""
    db.run_migrations()
    version = classifier_mod.prompt_version()
    classified = 0
    with db.connect() as conn:
        if prospect_id is not None:
            rows = conn.execute(
                "SELECT * FROM prospects WHERE id = ?", (prospect_id,)
            ).fetchall()
            if not rows:
                raise typer.BadParameter(f"prospect {prospect_id} not found")
            from src.db import _row_to_prospect  # type: ignore[attr-defined]

            prospects = [_row_to_prospect(r) for r in rows]
        elif all_:
            prospects = db.list_prospects(conn)
        else:
            prospects = db.list_prospects_needing_classification(conn)

        for p in prospects:
            output = classifier_mod.classify(p)
            db.insert_classification(
                conn,
                prospect_id=p.id,
                output=output,
                model_used=classifier_mod.STUB_MODEL_NAME,
                prompt_version=version,
            )
            classified += 1

    log.info("classify.done", classified=classified, prompt_version=version)
    typer.echo(f"classified={classified} prompt_version={version}")


@app.command("sync-sheet")
def sync_sheet() -> None:
    """Push system-owned columns to the configured Google Sheet."""
    db.run_migrations()
    from src.output import google_sheet

    with db.connect() as conn:
        n = google_sheet.sync(conn)
    typer.echo(f"rows_written={n}")


@app.command()
def report() -> None:
    """Print a summary: counts by tier, source, status; spend so far."""
    db.run_migrations()
    with db.connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM prospects").fetchone()[0]
        by_tier = conn.execute(
            """
            SELECT COALESCE(c.tier, 'unclassified') AS tier, COUNT(*) AS n
            FROM prospects p
            LEFT JOIN latest_classifications c ON c.prospect_id = p.id
            GROUP BY tier
            ORDER BY tier
            """
        ).fetchall()
        by_source = conn.execute(
            """
            SELECT source, COUNT(DISTINCT prospect_id) AS n
            FROM source_records
            GROUP BY source
            ORDER BY n DESC
            """
        ).fetchall()
        by_status = conn.execute(
            """
            SELECT COALESCE(status, 'not_contacted') AS status, COUNT(*) AS n
            FROM prospects p
            LEFT JOIN outreach_status o ON o.prospect_id = p.id
            GROUP BY status
            ORDER BY n DESC
            """
        ).fetchall()
        spend = conn.execute(
            """
            SELECT COALESCE(SUM(cost_usd), 0)
            FROM api_call_log
            WHERE timestamp >= date('now', 'start of month')
            """
        ).fetchone()[0]

    typer.echo(f"prospects total: {total}")
    typer.echo("by tier:")
    for r in by_tier:
        typer.echo(f"  {r['tier']}: {r['n']}")
    typer.echo("by source:")
    for r in by_source:
        typer.echo(f"  {r['source']}: {r['n']}")
    typer.echo("by status:")
    for r in by_status:
        typer.echo(f"  {r['status']}: {r['n']}")
    typer.echo(f"spend (this month, USD): {spend:.2f}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()

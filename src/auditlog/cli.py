"""Typer CLI for the audit logging pipeline."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from auditlog.service import AuditLogger

app = typer.Typer(help="Audit logging pipeline CLI.")
console = Console()


@app.command()
def append(
    db: str = typer.Option(..., "--db", help="Path to SQLite DB file."),
    actor: str = typer.Option(..., "--actor", help="Actor identifier."),
    action: str = typer.Option(..., "--action", help="Action name."),
    target: str = typer.Option(..., "--target", help="Target identifier."),
    result: str = typer.Option(..., "--result", help="Result status."),
    context: str = typer.Option(..., "--context", help="JSON object string for context."),
) -> None:
    """Append one event to the audit log."""
    try:
        context_obj = json.loads(context)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"--context must be valid JSON: {exc}") from exc

    if not isinstance(context_obj, dict):
        raise typer.BadParameter("--context must decode to a JSON object.")

    logger = AuditLogger(db)
    record = logger.append(
        actor=actor,
        action=action,
        target=target,
        result=result,
        context=context_obj,
    )
    console.print(f"Appended event id={record['id']} hash={record['event_hash']}")


@app.command("query")
def query_cmd(
    db: str = typer.Option(..., "--db", help="Path to SQLite DB file."),
    actor: str | None = typer.Option(None, "--actor", help="Filter by actor."),
    action: str | None = typer.Option(None, "--action", help="Filter by action."),
    limit: int = typer.Option(20, "--limit", min=1, help="Max rows to return."),
) -> None:
    """Query audit events."""
    logger = AuditLogger(db)
    events = logger.query(actor=actor, action=action, limit=limit)

    table = Table(title="Audit Events")
    table.add_column("id", justify="right")
    table.add_column("ts")
    table.add_column("actor")
    table.add_column("action")
    table.add_column("target")
    table.add_column("result")
    table.add_column("context_json")
    table.add_column("prev_hash")
    table.add_column("event_hash")

    for event in events:
        table.add_row(
            str(event["id"]),
            event["ts"],
            event["actor"],
            event["action"],
            event["target"],
            event["result"],
            event["context_json"],
            event["prev_hash"],
            event["event_hash"],
        )

    console.print(table)


@app.command()
def verify(
    db: str = typer.Option(..., "--db", help="Path to SQLite DB file."),
) -> None:
    """Verify hash chain integrity."""
    logger = AuditLogger(db)
    issues = logger.verify_chain()

    if not issues:
        console.print("OK")
        return

    console.print("FAIL")
    for issue in issues:
        console.print(f"- {issue}")
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

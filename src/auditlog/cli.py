"""CLI scaffold for the auditlog package."""

import typer

app = typer.Typer(help="Audit logging pipeline CLI scaffold.")


@app.callback()
def main() -> None:
    """Top-level CLI callback."""
    return None


if __name__ == "__main__":
    app()

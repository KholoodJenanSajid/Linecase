"""Spare-parts catalog parsed from the corpus.

Bin locations and part names are facts, not judgement calls, so the model is
never the authority on them. `reconcile` rewrites whatever the agent proposed
to match `data/corpus/parts-catalog.md` and flags SKUs that do not exist.
"""

from __future__ import annotations

from pathlib import Path

CATALOG_FILE = (
    Path(__file__).resolve().parents[1] / "data" / "corpus" / "parts-catalog.md"
)

_CATALOG: dict[str, dict[str, str]] | None = None


def catalog() -> dict[str, dict[str, str]]:
    global _CATALOG
    if _CATALOG is not None:
        return _CATALOG
    rows: dict[str, dict[str, str]] = {}
    for line in CATALOG_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0].lower() == "sku":
            continue
        rows[cells[0].upper()] = {
            "sku": cells[0],
            "name": cells[1],
            "bin": cells[2],
            "lead": cells[3] if len(cells) > 3 else "",
        }
    _CATALOG = rows
    return rows


def reconcile(parts: list[dict]) -> tuple[list[dict], list[str]]:
    """Return catalog-true parts plus notes on anything corrected or unknown."""
    known = catalog()
    fixed: list[dict] = []
    notes: list[str] = []
    for part in parts:
        sku = str(part.get("sku", "")).strip()
        row = known.get(sku.upper())
        if row is None:
            notes.append(f"unknown SKU {sku or '(blank)'} - supervisor to confirm")
            fixed.append({**part, "bin": "VERIFY", "sku": sku or "UNKNOWN"})
            continue
        if part.get("bin") != row["bin"]:
            notes.append(
                f"corrected bin for {row['sku']}: {part.get('bin')} -> {row['bin']}"
            )
        fixed.append(
            {
                "sku": row["sku"],
                "name": row["name"],
                "bin": row["bin"],
                "qty": int(part.get("qty") or 1),
            }
        )
    return fixed, notes

"""
experiments/tables.py — ``tables.md`` is generated, never written (D48).

The rule this module exists to enforce: **every number in the table is a
scalar that is already in ``metrics.json``.** Not derived here, not rounded
from something else, not remembered from a paper. ``verify`` checks it by
stripping the strings the metrics file contains — paths, hashes, commands,
names — and then asserting that every numeric token left over is one of the
metrics' own numbers, rendered by the one formatter below.

That check is worth more than it looks. The failure it prevents is not a typo;
it is the quiet one, where a table gains a plausible figure for a dataset that
was never on the machine. So a dataset that is absent gets a row saying
:data:`NOT_RUN` and no numbers at all, and a result with no sha256 is refused
outright — a number whose input cannot be identified is not a result.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

# What a row says when the dataset is not on this machine (D48).
NOT_RUN = "ishga tushirilmagan — ma’lumot yo‘q"

# Length of the sha256 prefix shown in a result row; the full hash is in the
# source block below the table and in metrics.json.
SHA_PREFIX = 12

# The only numbers the generated prose may contain: references to chapter II
# and to the thesis's own sections. Declared here rather than pattern-matched,
# so adding a number to the narrative is a visible edit to this list and not
# something that happens by accident. A result number can never enter this
# way: ``test_tables.py`` pins the contents of this set.
CITATIONS: frozenset[str] = frozenset({
    "2.2",   # Algorithm 2.2 — the topological order and lev
    "2.3",   # Algorithm 2.3 — the readiness update
    "3.3",   # section 3.3 of the thesis, where these tables go
})

_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def fmt(value: float | int) -> str:
    """
    The one way a number becomes text in a table.

    ``verify`` builds its allow-list with this same function, so the check is
    exact rather than a guess at the formatting.
    """
    if isinstance(value, bool):
        return "ha" if value else "yo‘q"
    if isinstance(value, int):
        return str(value)
    text = f"{value:.3f}".rstrip("0").rstrip(".")
    return text or "0"


# ---------------------------------------------------------------------------
# Walking a metrics document
# ---------------------------------------------------------------------------

def _scalars(node: Any) -> Iterator[Any]:
    if isinstance(node, dict):
        for value in node.values():
            yield from _scalars(value)
    elif isinstance(node, (list, tuple)):
        for value in node:
            yield from _scalars(value)
    else:
        yield node


def allowed_numbers(metrics: dict) -> set[str]:
    """Every numeric scalar of the metrics, in both its raw and rendered form."""
    out: set[str] = set()
    for value in _scalars(metrics):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        out.add(str(value))
        out.add(fmt(value))
    return out


def allowed_strings(metrics: dict) -> set[str]:
    """
    Every string scalar, plus the sha256 prefixes a row may show. These are
    removed from the markdown before the numeric scan, so a hash or a path
    does not look like a hand-written number.
    """
    out: set[str] = set()
    for value in _scalars(metrics):
        if not isinstance(value, str) or not value:
            continue
        out.add(value)
        if _SHA256.match(value):
            out.add(value[:SHA_PREFIX])
    return out


def verify(markdown: str, metrics: dict) -> list[str]:
    """
    Numeric tokens in ``markdown`` that are not numbers of ``metrics``.

    An empty list is the invariant of D48. Anything in it is a number that
    entered the table from somewhere other than the run — except the chapter
    and algorithm references of :data:`CITATIONS`, which are declared.
    """
    stripped = markdown
    for text in sorted(allowed_strings(metrics), key=len, reverse=True):
        stripped = stripped.replace(text, " ")
    permitted = allowed_numbers(metrics) | CITATIONS
    return [token for token in _NUMBER.findall(stripped) if token not in permitted]


def require_sources(metrics: dict) -> None:
    """
    Refuse to render a result whose input cannot be identified (D48).

    Every entry that reports numbers must name the file it read and that
    file's sha256; an entry that reports nothing (``status != "ok"``) needs
    neither, because it is the row that says the dataset was absent.
    """
    missing = []
    for entry in metrics.get("graphs", []) + metrics.get("datasets", []):
        if entry.get("status") != "ok":
            continue
        source = entry.get("source") or {}
        if not source.get("sha256"):
            missing.append(entry.get("name", "?"))
    if missing:
        raise ValueError(
            "a result with no source sha256 cannot be written (D48): "
            + ", ".join(missing)
        )


# ---------------------------------------------------------------------------
# The graph report's table
# ---------------------------------------------------------------------------

GRAPH_COLUMNS: tuple[tuple[str, str], ...] = (
    ("nodes", "Tugun"),
    ("raw_edges", "Fayldagi qirra"),
    ("edges", "Qirra"),
    ("self_loops", "O‘z-o‘ziga"),
    ("isolated", "Izolyatsiyalangan"),
    ("is_dag", "DAG"),
    ("weak_components", "Kuchsiz komp."),
    ("redundant_edges", "Ortiqcha"),
    ("longest_path", "Eng uzun yo‘l"),
)


def render_graph_report(metrics: dict) -> str:
    """``tables.md`` for ``graph_report.py``, generated from the metrics alone."""
    require_sources(metrics)
    provenance = metrics.get("provenance", {})
    lines: list[str] = [
        "# Graf tahlili — 3.3-bo‘limga qo‘yishga tayyor",
        "",
        "Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q;",
        "`experiments/tests/test_tables.py` har bir sonning `metrics.json` da borligini",
        "tekshiradi. Ma’lumoti yo‘q graf uchun qator soni emas, holati chiqadi.",
        "",
        "## 1. Graf o‘lchamlari va Y3",
        "",
        "| Graf | Yo‘nalish | " + " | ".join(label for _, label in GRAPH_COLUMNS) + " | sha256 |",
        "|---|---|" + "---|" * (len(GRAPH_COLUMNS) + 1),
    ]

    for entry in metrics.get("graphs", []):
        name = entry.get("name", "?")
        direction = entry.get("edge_direction", "—")
        if entry.get("status") != "ok":
            lines.append(
                f"| {name} | {direction} | "
                + " | ".join([NOT_RUN] + ["—"] * (len(GRAPH_COLUMNS) - 1))
                + " | — |"
            )
            continue
        cells = [fmt(entry[key]) if key in entry else "—" for key, _ in GRAPH_COLUMNS]
        sha = (entry.get("source") or {}).get("sha256", "")
        lines.append(f"| {name} | {direction} | " + " | ".join(cells) + f" | `{sha[:SHA_PREFIX]}` |")

    lines += _redundant_section(metrics)
    lines += _scc_section(metrics)
    lines += _readiness_section(metrics)
    lines += _sources_section(metrics, provenance)
    return "\n".join(lines) + "\n"


def _redundant_section(metrics: dict) -> list[str]:
    """Transitively redundant edges, by name — reported, never removed (GR3)."""
    lines = ["", "## 2. Tranzitiv ortiqcha qirralar", ""]
    any_shown = False
    for entry in metrics.get("graphs", []):
        if entry.get("status") != "ok":
            continue
        pairs = entry.get("redundant_edge_list") or []
        lines.append(
            f"**{entry.get('name', '?')}** [{entry.get('edge_direction', '—')}] — "
            f"{fmt(entry.get('redundant_edges', 0))}"
        )
        lines.append("")
        if not pairs:
            lines.append("- yo‘q")
        for source, target in pairs:
            lines.append(f"- `{source}` → `{target}`")
        lines.append("")
        any_shown = True
    if not any_shown:
        lines.append("Hech bir graf ishga tushirilmadi.")
        lines.append("")
    return lines


def _scc_section(metrics: dict) -> list[str]:
    """Y3: if a graph is cyclic, which components were merged."""
    cyclic = [
        entry for entry in metrics.get("graphs", [])
        if entry.get("status") == "ok" and not entry.get("is_dag", True)
    ]
    lines = ["## 3. Y3 — sikl va kuchli bog‘langan komponentlar", ""]
    if not cyclic:
        lines += ["Ishga tushirilgan graflarning hammasi asiklik; birlashtirish bo‘lmadi.", ""]
        return lines
    for entry in cyclic:
        merged = entry.get("scc_merged") or []
        lines.append(
            f"**{entry.get('name', '?')}** — {fmt(entry.get('scc_nontrivial', 0))} ta komponent "
            f"birlashtirildi, {fmt(entry.get('scc_merged_nodes', 0))} tugun"
        )
        lines.append("")
        for group in merged:
            lines.append("- " + ", ".join(f"`{member}`" for member in group))
        lines.append("")
    return lines


def _readiness_section(metrics: dict) -> list[str]:
    """Algorithm 2.3 incrementally against the O(n + m) rebuild."""
    lines = [
        "## 4. Tayyorlik yangilanishi: inkremental va to‘liq qayta hisoblash",
        "",
        "Bitta javobdan keyin Algoritm 2.3 faqat |Succ(v)| tugunni ko‘radi; TY6 ning",
        "to‘liq qayta hisoblashi har bir tugunni ko‘radi. Vaqtlar mashinaga bog‘liq,",
        "shuning uchun ular testda tasdiqlanmaydi — tasdiqlanadigan narsa: inkremental",
        "yo‘l ko‘radigan tugunlar soni to‘liqdan kichik yoki teng.",
        "",
        "| Graf | Yo‘nalish | Namuna | Takror | Inkremental tugun (median) | To‘liq tugun | "
        "Inkremental µs (median / p95) | To‘liq µs (median / p95) | Tezlashish (median) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for entry in metrics.get("graphs", []):
        name = entry.get("name", "?")
        direction = entry.get("edge_direction", "—")
        if entry.get("status") != "ok" or not entry.get("readiness"):
            lines.append(f"| {name} | {direction} | " + " | ".join([NOT_RUN] + ["—"] * 6) + " |")
            continue
        r = entry["readiness"]
        lines.append(
            f"| {name} | {direction} | {fmt(r['samples'])} | {fmt(r['repeats'])} | "
            f"{fmt(r['incremental_touched_median'])} | {fmt(r['full_touched'])} | "
            f"{fmt(r['incremental_us_median'])} / {fmt(r['incremental_us_p95'])} | "
            f"{fmt(r['full_us_median'])} / {fmt(r['full_us_p95'])} | "
            f"{fmt(r['speedup_median'])}× |"
        )
    lines.append("")
    return lines


def _sources_section(metrics: dict, provenance: dict) -> list[str]:
    """The four facts of D48, in full, under the tables that rest on them."""
    lines = ["## 5. Manba va ishga tushirish (D48)", ""]
    commit = provenance.get("code_commit") or "—"
    dirty = " (kuzatilmagan o‘zgarishlar bilan)" if provenance.get("code_dirty") else ""
    lines += [
        f"- kod commit'i: `{commit}`{dirty}",
        f"- buyruq: `{provenance.get('command', '—')}`",
        f"- vaqt: {provenance.get('created_at', '—')}",
        f"- python: {provenance.get('python', '—')}, {provenance.get('platform', '—')}",
    ]
    seeds = provenance.get("seeds") or {}
    if seeds:
        lines.append("- seed: " + ", ".join(f"{k} = {fmt(v)}" for k, v in sorted(seeds.items())))
    env = provenance.get("env") or {}
    if env:
        lines.append("- muhit: " + ", ".join(f"`{k}={v}`" for k, v in sorted(env.items())))
    packages = provenance.get("packages") or {}
    if packages:
        lines.append("- paketlar: " + ", ".join(f"{k} {v}" for k, v in sorted(packages.items())))
    lines.append("")

    lines += ["| Fayl | sha256 | Bayt |", "|---|---|---|"]
    for source in provenance.get("sources", []):
        lines.append(f"| `{source['name']}` | `{source['sha256']}` | {fmt(source['bytes'])} |")
    if not provenance.get("sources"):
        lines.append("| — | — | — |")
    lines.append("")
    return lines


def write(directory: Path, metrics: dict, env_txt: str, *, renderer=render_graph_report) -> dict[str, Path]:
    """
    Write ``metrics.json``, ``tables.md`` and ``env.txt`` into ``directory``.

    The table is rendered first and verified before anything is written, so a
    run that would have produced an untraceable number produces no files.
    """
    require_sources(metrics)
    markdown = renderer(metrics)
    strays = verify(markdown, metrics)
    if strays:
        raise ValueError(
            "tables.md would contain numbers that are not in metrics.json (D48): "
            + ", ".join(sorted(set(strays)))
        )

    directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "metrics": directory / "metrics.json",
        "tables": directory / "tables.md",
        "env": directory / "env.txt",
    }
    paths["metrics"].write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["tables"].write_text(markdown, encoding="utf-8")
    paths["env"].write_text(env_txt, encoding="utf-8")
    return paths

"""
benchmarks/rooted_tables.py — ``tables.md`` for D74, from ``metrics.json`` alone.

D48 applies here exactly as everywhere else: every number below is a scalar
that is already in the metrics document, rendered by ``tables.fmt``, and
``tables.write`` refuses to write the file if a token in it is not. The
renderer is passed to ``tables.write`` rather than added to
``experiments/tables.py``, so no committed result's renderer changes.

Note on the check's strength. ``tables.verify`` runs its generic scan — no
token that is not one of the metrics' own numbers survives — but not a
positional check: those are keyed by ``report`` in ``experiments/tables.py``
and D74 adds no key there. So the guarantee is "every number comes from the
run", not yet "every cell holds the number of its own key".
"""

from __future__ import annotations

from benchmarks.models import CTE, MPTT
from benchmarks.rooted import CTE_ROOTED, READING_METHODS
from experiments.tables import (
    _cell,
    _git_state_lines,
    _sources_section,
    _tree_warning,
    fmt,
)

_LABEL = {MPTT: "MPTT", CTE: "CTE", CTE_ROOTED: "CTE-rooted"}


def _ratio_cell(entry: dict) -> str:
    """ρ [CI], or a dash when the cell carries no interval."""
    if not entry or entry.get("ratio") is None:
        return "—"
    low, high = entry.get("ci_low"), entry.get("ci_high")
    if low is None or high is None:
        return _cell(entry["ratio"])
    return f"{fmt(entry['ratio'])} [{fmt(low)}; {fmt(high)}]"


def _median(cell: dict, method: str) -> str:
    measured = cell["methods"].get(method) or {}
    if measured.get("status") != "ok":
        return str(measured.get("status", "—"))
    return _cell(measured["seconds"]["median_ms"])


def _p95(cell: dict, method: str) -> str:
    measured = cell["methods"].get(method) or {}
    if measured.get("status") != "ok":
        return str(measured.get("status", "—"))
    return _cell(measured["seconds"]["p95_ms"])


def _queries(cell: dict, method: str) -> str:
    measured = cell["methods"].get(method) or {}
    if measured.get("status") != "ok":
        return "—"
    return _cell(measured.get("queries_median"))


def render(metrics: dict) -> str:
    """``tables.md`` for ``manage.py run_rooted_benchmark`` (D74)."""
    provenance = metrics.get("provenance", {})
    settings = metrics.get("settings") or {}
    reading = metrics.get("reading") or {}
    cells = metrics.get("cells") or []
    environment = metrics.get("environment") or {}
    postgres = environment.get("postgres") or {}

    lines: list[str] = [
        "# H4 (D74) — uchinchi o‘qish usuli: so‘ralgan tugundan boshlanadigan CTE",
        "",
        "Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.",
    ]
    lines += _tree_warning(provenance)
    lines += [
        "",
        "Uchala usul bir xil daraxtni o‘qiydi. `MPTT` — oraliq kodlash (django-mptt);",
        "`CTE` — django-tree-queries, rekursiya jadvaldagi barcha ildizlardan boshlanadi;",
        "`CTE-rooted` — qo‘lda yozilgan rekursiv CTE, rekursiya **so‘ralgan tugundan**",
        "boshlanadi. Jadval ikkinchi va uchinchi usulda bitta: `CteNode`, ya’ni farq",
        "faqat so‘rovning shaklida (D74).",
        "",
        "Yozish amallari o‘lchanmaydi: ular `CTE` bilan aynan bir xil kod.",
        "",
        "Oraliq — juftlashtirilgan bootstrap "
        f"({_cell(settings.get('replicates'))} replika, "
        f"{_cell(settings.get('confidence_percent'))} %): har takrorda uchala usul",
        "bir xil nishon tugunda ishlagan (D63).",
    ]
    if metrics.get("quick"):
        lines += [
            "",
            "> **`--quick` ishga tushirish — dissertatsiya natijasi emas.** Bu quvurni",
            "> sinash uchun: kichik daraxt va kam takror. To‘liq natija uchun",
            "> `manage.py run_rooted_benchmark` bayroqsiz ishga tushiriladi.",
        ]

    lines += [
        "",
        "## 1. O‘qish amallari — uch usul",
        "",
        "| Shakl | Hajm | Amal | MPTT mediana (ms) | CTE mediana (ms) | CTE-rooted mediana (ms) |",
        "|---|---|---|---|---|---|",
    ]
    for cell in cells:
        lines.append("| " + " | ".join([
            cell["shape"], _cell(cell["size"]), cell["label"],
            *(_median(cell, method) for method in READING_METHODS),
        ]) + " |")

    lines += [
        "",
        "## 2. Nisbatlar",
        "",
        "ρ = mediana(CTE-rooted) / mediana(boshqa usul): ρ < 1 — CTE-rooted tezroq.",
        "",
        "| Shakl | Hajm | Amal | ρ rooted/MPTT [CI] | ρ rooted/CTE [CI] |",
        "|---|---|---|---|---|",
    ]
    for cell in cells:
        ratios = cell.get("ratios") or {}
        lines.append("| " + " | ".join([
            cell["shape"], _cell(cell["size"]), cell["label"],
            _ratio_cell(ratios.get(f"{CTE_ROOTED}_over_{MPTT}")),
            _ratio_cell(ratios.get(f"{CTE_ROOTED}_over_{CTE}")),
        ]) + " |")

    lines += [
        "",
        "## 3. Dumi (p95) va SQL so‘rovlar",
        "",
        "p95 da’voga kirmaydi (D63). So‘rovlar soni — `CaptureQueriesContext`,",
        "har takrorda; uchala usulda ham tugun avval alohida so‘rov bilan olinadi.",
        "",
        "| Shakl | Hajm | Amal | MPTT p95 | CTE p95 | CTE-rooted p95 | MPTT SQL | CTE SQL | CTE-rooted SQL |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for cell in cells:
        lines.append("| " + " | ".join([
            cell["shape"], _cell(cell["size"]), cell["label"],
            *(_p95(cell, method) for method in READING_METHODS),
            *(_queries(cell, method) for method in READING_METHODS),
        ]) + " |")

    lines += [
        "",
        "## 4. To‘g‘rilik tekshiruvi (D74)",
        "",
        "Har bir shakl uchun dastlabki nishonlarda qaytgan `id` lar to‘plami",
        "kutubxonaning `descendants()` / `ancestors()` natijasi bilan solishtirildi.",
        "Mos kelmagan tekshiruv bo‘lsa, o‘lchov umuman yozilmaydi.",
        "",
        f"- tekshiruvlar soni: {_cell(metrics.get('equivalence_checks'))}",
        f"- mos kelmaganlari: {_cell(metrics.get('equivalence_failures'))}",
        "",
        "## 5. O‘qish qoidasi (D74, natijadan oldin belgilangan)",
        "",
        f"> {reading.get('rule', '—')}",
        "",
        f"- chegara: {_cell(reading.get('limit'))}",
        f"- o‘lchangan kataklar: {_cell(reading.get('cells_measured'))}",
        f"- o‘lchanmagan kataklar: {_cell(reading.get('cells_not_measured'))}",
        f"- chegaradan oshgan kataklar: {_cell(reading.get('cells_over_limit_count'))}",
        "",
        f"**Natija: {reading.get('status', '—')}**",
        "",
    ]
    over = reading.get("cells_over_limit") or []
    if over:
        lines += [
            "Chegaradan oshgan kataklar:",
            "",
            "| Shakl | Hajm | Amal | ρ rooted/MPTT |",
            "|---|---|---|---|",
        ]
        for item in over:
            lines.append(
                f"| {item['shape']} | {_cell(item['size'])} | {item['operation']} "
                f"| {_cell(item['ratio'])} |"
            )
        lines.append("")

    lines += [
        "H4 ning hukmi bu o‘lchovdan o‘zgarmaydi: u D63 da natijadan oldin",
        "belgilangan qoida bo‘yicha chiqarilgan. Bu yerda faqat dissertatsiyaning",
        "tavsiyasi tekshiriladi.",
        "",
        "## 6. Daraxtlar",
        "",
        "| Usul | Shakl | Hajm | Tugun | Maks. chuqurlik | sha256 |",
        "|---|---|---|---|---|---|",
    ]
    for tree in metrics.get("trees") or []:
        lines.append(
            f"| {tree['method']} | {tree['shape']} | {_cell(tree['size'])} "
            f"| {_cell(tree['nodes'])} | {_cell(tree['max_depth'])} "
            f"| `{tree['sha256'][:12]}` |"
        )

    lines += [
        "",
        "## 7. Muhit",
        "",
        f"- PostgreSQL: {postgres.get('version', '—')}",
        f"- baza: `{(metrics.get('database') or {}).get('name', '—')}`",
        f"- umumiy vaqt (soniya): {_cell(metrics.get('total_seconds'))}",
        "",
    ]
    lines += _sources_section(metrics, provenance, number=8)
    return "\n".join(lines) + "\n"


__all__ = ["render"]

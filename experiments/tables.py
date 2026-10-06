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

# What a row says when the *model* cannot run on data that is present — such
# as BKT+IRT+Pre without a prerequisite graph. A different sentence, because a
# different thing is missing, and the reason is given once rather than twice.
NOT_APPLICABLE = "ishga tushirilmadi"

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
    "2.4",   # Algorithm 2.4 — the per-answer update the models run
    "3.3",   # section 3.3 of the thesis, where these tables go
    "2016",  # Xiong et al., EDM 2016 — the DKT sanity range
})

_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_NUMERIC_TEXT = re.compile(r"^-?\d+(?:\.\d+)?$")


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
    """
    Every numeric scalar of the metrics, in both its raw and rendered form.

    A *string* that is a number is counted here too, not stripped as text: ids
    in this data are strings ("47" is a skill), and removing them from the
    markdown would cut a hole in the middle of a real number — stripping "47"
    turns 47 037 into 037, which then looks like a figure from nowhere.
    """
    out: set[str] = set()
    for value in _scalars(metrics):
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            out.add(str(value))
            out.add(fmt(value))
        elif isinstance(value, str) and _NUMERIC_TEXT.match(value):
            out.add(value)
            try:
                out.add(fmt(float(value) if "." in value else int(value)))
            except ValueError:  # pragma: no cover - the regex already matched
                pass
    return out


def allowed_strings(metrics: dict) -> set[str]:
    """
    Every string scalar, plus the sha256 prefixes a row may show. These are
    removed from the markdown before the numeric scan, so a hash or a path
    does not look like a hand-written number.
    """
    out: set[str] = set()
    for value in _scalars(metrics):
        if not isinstance(value, str) or len(value) < 2:
            continue
        # A numeric string is a number, not text: see allowed_numbers.
        if _NUMERIC_TEXT.match(value):
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
    entries = list(metrics.get("graphs", [])) + list(metrics.get("datasets", []))
    dataset = metrics.get("dataset")
    if isinstance(dataset, dict):
        entries.append(dataset)
    missing = []
    for entry in entries:
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
    lines += _sources_section(metrics, provenance, number=5)
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


def _sources_section(metrics: dict, provenance: dict, number: int = 5) -> list[str]:
    """The four facts of D48, in full, under the tables that rest on them."""
    lines = [f"## {number}. Manba va ishga tushirish (D48)", ""]
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


# ---------------------------------------------------------------------------
# The H2 table (D53)
# ---------------------------------------------------------------------------

MODEL_ORDER: tuple[str, ...] = (
    "BKT",
    "BKT+IRT (λ=0)",
    "BKT+IRT+Pre",
    "Elo/Rasch",
    "PFA",
    "DKT",
    "AKT",
)


def render_h2_report(metrics: dict) -> str:
    """``tables.md`` for ``h2.py``, generated from the metrics alone (D48)."""
    require_sources(metrics)
    provenance = metrics.get("provenance", {})
    pooled = metrics.get("pooled", {}).get("models", {})
    unavailable = {entry["model"]: entry["reason"] for entry in metrics.get("unavailable", [])}

    quick = metrics.get("quick")
    label = (metrics.get("dataset") or {}).get("label", "")
    lines: list[str] = [
        f"# H2 — {label}: modellarni solishtirish",
        "",
        "Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.",
    ]
    if quick:
        lines += [
            "",
            "> **`--quick` ishga tushirish — dissertatsiya natijasi emas.** Bu quvurni",
            "> sinash uchun: talabalarning bir qismi va kam epoch. To‘liq natija uchun",
            "> `python -m experiments.h2` bayroqsiz ishga tushiriladi.",
        ]
    lines += ["", "## 1. Pooled natija (barcha qismlar birga)", ""]
    lines += _h2_main_table(
        pooled, unavailable, metrics.get("pooled", {}).get("confidence_percent", 95),
    )
    lines += _h2_early_table(pooled)
    lines += _h2_comparisons(metrics)
    lines += _h2_folds(metrics)
    lines += _h2_sanity(metrics)
    lines += _h2_grid(metrics)
    lines += _h2_pybkt(metrics)
    lines += _h2_dataset(metrics)
    lines += _sources_section(metrics, provenance, number=9)
    return "\n".join(lines) + "\n"


def _auc_cell(entry: dict) -> str:
    interval = entry.get("auc_interval") or {}
    auc = entry.get("scores", {}).get("all", {}).get("auc")
    if auc is None:
        return "—"
    low, high = interval.get("ci_low"), interval.get("ci_high")
    if low is None or high is None:
        return fmt(auc)
    return f"{fmt(auc)} [{fmt(low)}, {fmt(high)}]"


def _h2_main_table(pooled: dict, unavailable: dict, confidence_percent) -> list[str]:
    lines = [
        f"AUC uchun {fmt(confidence_percent)}% ishonch oralig‘i — talabalar bo‘yicha "
        "bootstrap (javoblar talaba ichida klasterlangan).",
        "",
        "| Model | AUC [95% CI] | RMSE | Aniqlik | Javob |",
        "|---|---|---|---|---|",
    ]
    for name in MODEL_ORDER:
        if name in unavailable:
            lines.append(
                f"| {name} | {NOT_APPLICABLE}: {unavailable[name]} | — | — | — |"
            )
            continue
        entry = pooled.get(name)
        if entry is None:
            continue
        all_scores = entry.get("scores", {}).get("all", {})
        lines.append(
            f"| {name} | {_auc_cell(entry)} | {fmt(all_scores.get('rmse', 0))} | "
            f"{fmt(all_scores.get('accuracy', 0))} | {fmt(all_scores.get('n', 0))} |"
        )
    lines.append("")
    return lines


def _h2_early_table(pooled: dict) -> list[str]:
    lines = [
        "## 2. Dastlabki urinishlar (AUC)",
        "",
        "Har bir talabaning birinchi k javobi alohida. Prerekvizitga asoslangan",
        "boshlang‘ich qiymat faqat shu yerda ta’sir ko‘rsatishi mumkin: o‘ninchi",
        "javobda dalil har qanday priordan ustun bo‘lib ketadi.",
        "",
        "`Tarixsiz` — modelning tarixdan bashorat qila olmagan javoblari soni:",
        "ular base rate bilan baholanadi. Ketma-ketlik modellarida har bir talaba",
        "uchun bitta shunday javob bor, ya’ni k = 3 ustunining uchdan biri doimiy",
        "qiymat — shuning uchun DKT va AKT ning dastlabki ustunlari modelga nisbatan",
        "pastroq o‘qiladi.",
        "",
        "| Model | Hammasi | Birinchi 3 | Birinchi 5 | Tarixsiz |",
        "|---|---|---|---|---|",
    ]
    for name in MODEL_ORDER:
        entry = pooled.get(name)
        if entry is None:
            continue
        scores = entry.get("scores", {})
        cells = []
        for key in ("all", "first_3", "first_5"):
            auc = scores.get(key, {}).get("auc")
            cells.append("—" if auc is None else fmt(auc))
        cells.append(fmt(entry.get("cold_rows", 0)))
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def _h2_comparisons(metrics: dict) -> list[str]:
    comparisons = metrics.get("pooled", {}).get("comparisons", [])
    lines = [
        "## 3. Juftlik solishtirishlari (DeLong, Holm tuzatmasi bilan)",
        "",
        "Juftlashgan test: ikki model bir xil javoblarda baholangan, shuning uchun",
        "AUC'lar orasidagi korrelyatsiya ayiriladi. Holm — butun juftliklar",
        "oilasi uchun.",
        "",
        "**Ikki cheklov ochiq aytiladi.**",
        "",
        "1. DeLong javoblarni mustaqil deb hisoblaydi, bu jadvaldagi prognozlar esa",
        "   besh qismdan birlashtirilgan va talaba ichida klasterlangan. Shuning uchun",
        "   bu yerdagi p qiymatlari haqiqiydan **kichik** bo‘lishi mumkin. 1-jadvaldagi",
        "   ishonch oralig‘i talabalar bo‘yicha bootstrap bilan olingan va shu",
        "   ma’noda ishonchliroq; DeLong juftliklarni tartiblash uchun ishlatiladi,",
        "   oralig‘ni belgilash uchun emas.",
        "2. BKT, BKT+IRT va BKT+IRT+Pre bir xil moslangan P0/PT/P(G)/P(S) ni",
        "   bo‘lishadi (`parameters.shared_by_flag_variants`). Ablatsiya bitta",
        "   narsani o‘zgartirishi kerak, shuning uchun bayroq o‘zgaradi, moslash",
        "   emas. Bu IRT variantlari uchun kichik noqulaylik: parametrlar ular uchun",
        "   optimallashtirilmagan.",
        "",
        "| A | B | AUC A | AUC B | Farq | z | p | p (Holm) | Muhim |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    if not comparisons:
        lines += ["| — | — | — | — | — | — | — | — | — |", ""]
        return lines
    for item in sorted(comparisons, key=lambda row: row.get("p", 1.0)):
        lines.append(
            f"| {item['a']} | {item['b']} | {fmt(item['auc_a'])} | {fmt(item['auc_b'])} | "
            f"{fmt(item['difference'])} | {fmt(item['z'])} | {_p(item['p'])} | "
            f"{_p(item['p_holm'])} | {fmt(bool(item['significant']))} |"
        )
    lines.append("")
    return lines


def _p(value) -> str:
    """A p value, in the metrics' own rendering so verify() can find it."""
    return "—" if value is None else fmt(value)


def _h2_folds(metrics: dict) -> list[str]:
    lines = [
        "## 4. Qismlar bo‘yicha AUC",
        "",
        "Bo‘lish talabalar bo‘yicha: bitta talabaning javoblari hech qachon",
        "o‘qitish va test to‘plamlariga bo‘linmaydi.",
        "",
    ]
    folds = metrics.get("folds", [])
    if not folds:
        return lines + ["Qism yo‘q.", ""]
    header = "| Model | " + " | ".join(f"{fold['index'] + 1}-qism" for fold in folds) + " |"
    lines += [header, "|---|" + "---|" * len(folds)]
    for name in MODEL_ORDER:
        cells = []
        present = False
        for fold in folds:
            entry = fold.get("models", {}).get(name, {})
            if entry.get("status") != "ok":
                cells.append("—")
                continue
            present = True
            auc = entry.get("scores", {}).get("all", {}).get("auc")
            cells.append("—" if auc is None else fmt(auc))
        if present:
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines.append("")
    return lines


def _h2_sanity(metrics: dict) -> list[str]:
    note = metrics.get("sanity") or {}
    lines = ["## 5. Aqlga muvofiqlik chegarasi (D53)", ""]
    if not note:
        return lines + ["Tekshirilmadi.", ""]
    auc = note.get("auc")
    low, high = note.get("expected_range", [None, None])
    lit_low, lit_high = note.get("literature_range", [None, None])
    lines += [
        f"- DKT AUC: {'—' if auc is None else fmt(auc)}",
        f"- kutilgan oraliq: {fmt(low)}–{fmt(high)}",
        f"- adabiyotdagi qiymat (Xiong va boshq., EDM 2016, takrorsiz): {fmt(lit_low)}–{fmt(lit_high)}",
        f"- oraliq ichidami: {'—' if note.get('within_range') is None else fmt(bool(note['within_range']))}",
    ]
    if note.get("within_range") is False:
        lines += [
            "",
            "> **Ogohlantirish.** DKT AUC takrorsiz ASSISTments 2009 uchun qayd etilgan",
            "> oraliqdan tashqarida. Jadvaldagi boshqa hech narsani o‘qishdan oldin",
            "> D50 tozalashini qayta tekshirish kerak. `--quick` ishga tushirishda bu",
            "> kutilgan: kam talaba va kam epoch bilan DKT to‘liq o‘qitilmaydi.",
        ]
    lines.append("")
    return lines


def _h2_grid(metrics: dict) -> list[str]:
    """Does the bounded grid search run into its own edges?"""
    check = metrics.get("grid_check") or {}
    lines = ["## 6. Grid tekshiruvi — moslash grid chetiga tegdimi", ""]
    if not check:
        return lines + ["Ishga tushirilmadi.", ""]

    bounds = check.get("bounds", {})
    lines += [
        "Eng yuqori ruxsat etilgan qiymatda to‘planib qolgan moslash — moslash emas,",
        "grid'ning “ma’lumot men bera oladigandan ko‘proq xohlaydi” deyishi.",
        "",
        "`P0` va `PT` uchun bu grid torligini bildiradi va grid kengaytirilishi kerak.",
        f"`P(G)` va `P(S)` uchun boshqa narsani: ularning shiftini grid emas, II bob",
        f"belgilaydi (G_MAX = {fmt(bounds.get('g_max', 0))}, S_MAX = {fmt(bounds.get('s_max', 0))}),",
        "chunki γ chegarada aniqlanmagan. Ya’ni u yerdagi to‘planish — chegara",
        "ishlayotgani, va grid'ni kengaytirish moslashni yaxshilamaydi, modelni buzadi.",
        "Shu ishga tushirishdagi pyBKT solishtirishi bunga tashqi dalil: uning EM'ida",
        "chegara yo‘q.",
        "",
        f"Jami moslash: {fmt(check.get('fits', 0))} "
        f"({fmt(check.get('folds', 0))} qismda)",
        "",
        "| Parametr | Ruxsat etilgan qiymatlar | Eng pastda | Eng yuqorida | Yuqoridagilar ulushi | Shiftni kim belgilaydi |",
        "|---|---|---|---|---|---|",
    ]
    labels = {"p0": "P0", "pt": "PT", "g0": "P(G)", "s0": "P(S)"}
    for name, entry in (check.get("parameters") or {}).items():
        values = ", ".join(fmt(value) for value in entry.get("admissible_values", []))
        ceiling = "II bob" if entry.get("ceiling_is_chapter_two") else "grid"
        lines.append(
            f"| {labels.get(name, name)} | {values} | "
            f"{fmt(entry.get('at_lowest', 0))} | {fmt(entry.get('at_highest', 0))} | "
            f"{fmt(entry.get('share_at_highest', 0))} | {ceiling} |"
        )
    lines.append("")
    return lines


def _h2_pybkt(metrics: dict) -> list[str]:
    check = metrics.get("pybkt_cross_check")
    lines = ["## 7. pyBKT bilan o‘zaro tekshiruv (D53)", ""]
    if not check:
        return lines + ["Ishga tushirilmadi.", ""]
    if check.get("status") == "unavailable":
        return lines + [f"{NOT_RUN} — {check.get('reason', '')}", ""]

    bounds = check.get("bounds", {})
    lines += [
        "Bir xil mavzular ikki marta moslanadi: `neuro_model.calibrate` ning",
        "chegaralangan grid search'i va pyBKT ning EM'i. Farqning tizimli sababi —",
        f"II bobning chegaralari (G_MAX = {fmt(bounds.get('g_max', 0))}, "
        f"S_MAX = {fmt(bounds.get('s_max', 0))}), pyBKT ularni bilmaydi. Ikkala",
        "parametr to‘plami bir xil ta’rif bilan baholanadi: `calibrate.log_likelihood`.",
        "",
        f"Chegaradan tashqarida chiqqan pyBKT baholari: "
        f"{fmt(check.get('pybkt_outside_bounds_count', 0))} / "
        f"{fmt(check.get('skills_compared', 0))}",
        "",
        "| Mavzu | Javob | P0 (grid / EM) | PT | P(G) | P(S) | logL (grid / EM) | EM chegaradan tashqarida |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for entry in check.get("comparisons", []):
        if entry.get("status") != "ok":
            lines.append(
                f"| {entry.get('skill', '?')} | {fmt(entry.get('answers', 0))} | "
                + " | ".join([NOT_RUN] + ["—"] * 5) + " |"
            )
            continue
        grid, em = entry["grid"], entry["pybkt"]
        outside = entry["pybkt_outside_bounds"]
        flags = [key.upper() for key, value in outside.items() if value]
        lines.append(
            f"| {entry['skill']} | {fmt(entry['answers'])} | "
            f"{fmt(grid['p0'])} / {fmt(em['p0'])} | {fmt(grid['pt'])} / {fmt(em['pt'])} | "
            f"{fmt(grid['g0'])} / {fmt(em['g0'])} | {fmt(grid['s0'])} / {fmt(em['s0'])} | "
            f"{fmt(entry['log_likelihood']['grid'])} / {fmt(entry['log_likelihood']['pybkt'])} | "
            f"{', '.join(flags) if flags else 'yo‘q'} |"
        )
    lines.append("")
    return lines


def _h2_dataset(metrics: dict) -> list[str]:
    dataset = metrics.get("dataset") or {}
    split = metrics.get("split") or {}
    cleaned = dataset.get("cleaned") or {}
    raw = dataset.get("raw") or {}
    lines = [
        "## 8. Ma’lumot va tozalash (D50)",
        "",
        f"- xom qatorlar: {fmt(raw.get('rows', 0))}, talabalar: {fmt(raw.get('students', 0))}, "
        f"bo‘sh `skill_id`: {fmt(raw.get('blank_skill_id', 0))}",
        f"- tozalangandan keyin: {fmt(cleaned.get('rows', 0))} qator, "
        f"{fmt(cleaned.get('students', 0))} talaba, {fmt(cleaned.get('skills', 0))} mavzu, "
        f"bir nechta skill'li `order_id`: {fmt(cleaned.get('multi_skill_orders', 0))}",
        f"- ishlatilgan: {fmt(dataset.get('answers_used', 0))} javob, "
        f"{fmt(dataset.get('learners_used', 0))} talaba",
        f"- `--original-only`: {fmt(bool(dataset.get('original_only')))}",
        f"- bo‘lish: {fmt(split.get('folds', 0))} qism, talabalar bo‘yicha, "
        f"validatsiya ulushi {fmt(split.get('validation_fraction', 0))}, "
        f"seed {fmt(split.get('seed', 0))}",
        f"- DKT/AKT epoch chegarasi: {fmt(metrics.get('epochs', 0))}",
        "",
        "Tozalash qoidalari (D50, o‘zgarmas):",
        "",
    ]
    for rule in dataset.get("cleaning_rules", []):
        lines.append(f"1. {rule}")
    lines.append("")
    return lines

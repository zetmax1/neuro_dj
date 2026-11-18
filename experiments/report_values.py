"""
experiments/report_values.py — the thesis values of REMEDIATION_REPORT.md, from metrics.json.

Every number in the report's values block is read here from a committed
result's ``metrics.json`` and rendered with ``tables.fmt`` (D48); nothing is
typed by hand. Two modes:

    python -m experiments.report_values --write REMEDIATION_REPORT.md   # (re)write the block
    python -m experiments.report_values --check REMEDIATION_REPORT.md   # verify it

``--check`` re-renders the block from the result files and compares it with
the report character for character, then checks every number of each section
against that section's own metrics: a number is either one of its scalars (as
``tables.verify`` accepts them) or one of the few values this script derives
(the parameter quartiles, the counts of failing cells), which the re-render
has just recomputed. It prints how many numbers it checked and exits 1 on any
difference.

Reads only experiments/results/; writes only the report's block.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from experiments.tables import _NUMBER, allowed_numbers, allowed_strings, fmt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "experiments" / "results"
START = "<!-- report-values:start (experiments/report_values.py; do not edit by hand) -->"
END = "<!-- report-values:end -->"

H2 = "assist09/20261010-060005"
D55 = "assist09-bounds/20261011-183756"
D60 = "assist09-frozen/20261012-063439"
H1 = "junyi-h1/20261019-102526"
H3 = "junyi-h3/20261019-122423"
H4 = "tree-benchmark/20261016-093916"
H4_DEEP = "tree-benchmark/20261020-050428"
LOCUST = "locust/20261020-100901"
LOCUST_RUNSERVER = ("locust/20261020-085406", "locust/20261020-085659")
PARAMETERS = ("p0", "pt", "g0", "s0")


def load(folder: str) -> dict:
    return json.loads((RESULTS / folder / "metrics.json").read_text(encoding="utf-8"))


def ci(estimate, low, high) -> str:
    return f"{fmt(estimate)} [{fmt(low)}; {fmt(high)}]"


def quartiles(distribution: dict[str, int]) -> tuple[float, float, float, int]:
    """Q1, median, Q3 of a {grid value: count} histogram (lower value at ties)."""
    values = sorted((float(v), n) for v, n in distribution.items())
    total = sum(n for _, n in values)

    def at(fraction: float) -> float:
        rank = fraction * (total - 1)
        seen = 0
        for value, count in values:
            seen += count
            if seen > rank:
                return value
        return values[-1][0]

    return at(0.25), at(0.5), at(0.75), total


# ---------------------------------------------------------------------------
# Sections: (title, source folders, markdown lines, derived numbers)
# ---------------------------------------------------------------------------

def h2() -> tuple[str, list[str], list[str], set[str]]:
    m = load(H2)
    lines = [
        "| Model | AUC [95 % CI] |",
        "|---|---|",
    ]
    for name, model in m["pooled"]["models"].items():
        i = model["auc_interval"]
        lines.append(f"| {name} | {ci(i['estimate'], i['ci_low'], i['ci_high'])} |")
    lines += ["", "| Kontrast | Qaror | Farq [95 % CI] | p (Holm) |", "|---|---|---|---|"]
    for c in m["pooled"]["contrasts"]:
        lines.append(
            f"| {c['a']} − {c['b']} | {c['decision']} | {ci(c['difference'], c['ci_low'], c['ci_high'])} "
            f"| {fmt(c['p_holm'])} |"
        )
    s = m["sanity"]
    lines.append(f"\nDKT sanity: AUC {fmt(s['auc'])}, kutilgan oraliqda: {fmt(s['within_range'])}.")
    return "H2 — ASSISTments 2009, 7 model (D57, D59)", [H2], lines, set()


def d55() -> tuple:
    m = load(D55)
    lines = [
        "| Sozlama | G_MAX | S_MAX | BKT+IRT − BKT [95 % CI] | BKT+IRT − DKT [95 % CI] |",
        "|---|---|---|---|---|",
    ]
    for s in m["settings"]:
        d, k = s["difference"]["bootstrap"], s["dkt_difference"]
        lines.append(
            f"| {s['name']} | {fmt(s['g_max'])} | {fmt(s['s_max'])} "
            f"| {ci(d['estimate'], d['ci_low'], d['ci_high'])} | {ci(k['estimate'], k['ci_low'], k['ci_high'])} |"
        )
    return "D55 — chegaralar sezgirligi (ASSISTments)", [D55], lines, set()


def d60() -> tuple:
    m = load(D60)
    lines = ["| Da’vo | current [95 % CI] | frozen [95 % CI] | Barqaror |", "|---|---|---|---|"]
    for key, claim in m["claims"].items():
        if not isinstance(claim, dict):
            continue
        cur, fro = claim["per_variant"]["current"], claim["per_variant"]["frozen"]
        lines.append(
            f"| {key}: {claim['statement']} | {ci(cur['difference'], cur['ci_low'], cur['ci_high'])} "
            f"| {ci(fro['difference'], fro['ci_low'], fro['ci_high'])} | {fmt(claim['robust'])} |"
        )
    return "D60 — test vaqtida qiyinlik muzlatilganda", [D60], lines, set()


def h1() -> tuple:
    m = load(H1)
    lines = [f"Holat: **{m['reading']['status']}**.", "", "| Qoida | Farq [95 % CI] | Xulosa |", "|---|---|---|"]
    for r in m["reading"]["per_rule"]:
        lines.append(f"| {r['rule']} | {ci(r['difference'], r['ci_low'], r['ci_high'])} | {r['verdict']} |")
    return "H1 — Junyi, tayyorlik qoidasi", [H1], lines, set()


def h3() -> tuple:
    m = load(H3)
    lines = ["| k | Kontrast | Farq [95 % CI] | Holat |", "|---|---|---|---|"]
    for k, pooled in m["pooled"].items():
        status = pooled["reading"]["status"]
        for c in pooled["contrasts"]:
            lines.append(f"| {k} | {c['a']} − {c['b']} | {ci(c['difference'], c['ci_low'], c['ci_high'])} | {status} |")
    lines.append(f"\nAsosiy k = {m['main_k']}.")
    return "H3 — Junyi, graf (BKT+IRT+Pre)", [H3], lines, set()


def h4() -> tuple:
    m, deep = load(H4), load(H4_DEEP)
    r = m["reading"]
    derived = {
        str(len(r["write_failures"])), str(len(r["read_failures"])),
        str(len(r["integrity_failures"])), str(len(r["not_computed"])),
    }
    lines = [
        f"Holat: **{r['status']}**. Yozish kataklari {fmt(r['write_cells'])}, “CTE tezroq” emas: "
        f"{len(r['write_failures'])}; o‘qish kataklari {fmt(r['read_cells'])}, "
        f"{fmt(r['read_tolerance'])} barobardan sekin: {len(r['read_failures'])}; "
        f"yaxlitlik buzilishi: {len(r['integrity_failures'])}; hisoblanmagan: {len(r['not_computed'])}.",
        "",
        "`deep_chain/100000`, qayta o‘lchangan (D63h):",
        "",
        "| Amal | ρ = MPTT / CTE [95 % CI] | Xulosa |",
        "|---|---|---|",
    ]
    for cell in deep["cells"]:
        ratio = cell.get("ratio") or {}
        value = ci(ratio["ratio"], ratio["ci_low"], ratio["ci_high"]) if ratio.get("ratio") is not None else "—"
        lines.append(f"| {cell['label']} | {value} | {cell['verdict']} |")
    return "H4 — saqlash usullari (D63)", [H4, H4_DEEP], lines, derived


def locust() -> tuple:
    m = load(LOCUST)
    run = m["run"]
    lines = [
        f"{run['server']}, {fmt(run['users'])} foydalanuvchi, {fmt(run['duration_s'])} s, DEBUG={fmt(run['debug'])}.",
        "",
        "| Endpoint | So‘rovlar | Xato ulushi | p50, ms | p95, ms | RPS |",
        "|---|---|---|---|---|---|",
    ]
    for name in ("next_question", "submit_answer", "trajectory", "Aggregated"):
        e = m["endpoints"][name]
        lines.append(
            f"| {name} | {fmt(e['requests'])} | {fmt(e['error_share'])} | {fmt(e['p50_ms'])} "
            f"| {fmt(e['p95_ms'])} | {fmt(e['rps'])} |"
        )
    lines.append(f"\nV-F2 mo‘ljali: p95 < {fmt(m['v_f2_target_ms'])} ms.")
    return "Locust — V-F2 (asosiy, D68a)", [LOCUST], lines, set()


def locust_runserver() -> tuple:
    lines = ["| Natija | Server | Foydalanuvchi | p95 (jami), ms | RPS |", "|---|---|---|---|---|"]
    for folder in LOCUST_RUNSERVER:
        m = load(folder)
        e = m["endpoints"]["Aggregated"]
        lines.append(
            f"| `{folder}` | {m['run']['server']} | {fmt(m['run']['users'])} | {fmt(e['p95_ms'])} | {fmt(e['rps'])} |"
        )
    return "Locust — runserver (qo‘shimcha, D68)", list(LOCUST_RUNSERVER), lines, set()


def parameters() -> tuple:
    m = load(H2)
    lines = [
        "| Parametr | Grid | Fit'lar | Q1 | Mediana | Q3 | Pastki chetda | Yuqori chetda |",
        "|---|---|---|---|---|---|---|---|",
    ]
    derived: set[str] = set()
    top = m["grid_check"]["parameters"]
    for name in PARAMETERS:
        summed: dict[str, int] = {}
        for fold in m["folds"]:
            for value, count in fold["parameters"]["grid_check"]["parameters"][name]["distribution"].items():
                summed[value] = summed.get(value, 0) + count
        q1, median, q3, total = quartiles(summed)
        derived |= {fmt(q1), fmt(median), fmt(q3), str(total)}
        p = top[name]
        lines.append(
            f"| {name} | {fmt(p['lowest'])}…{fmt(p['highest'])} | {total} | {fmt(q1)} | {fmt(median)} | {fmt(q3)} "
            f"| {fmt(p['share_at_lowest'])} | {fmt(p['share_at_highest'])} |"
        )
    lines.append(
        "\nJunyi (H1, H3): per-skill parametrlar `metrics.json` da saqlanmagan (`folds[].parameters` bo‘sh), "
        "taqsimotni qayta yugurishsiz berib bo‘lmaydi."
    )
    return "Kalibrlangan BKT parametrlari — ASSISTments (H2, 5 fold)", [H2], lines, derived


SECTIONS = (h2, d55, d60, h1, h3, h4, locust, locust_runserver, parameters)


def render() -> tuple[str, list[tuple[str, list[str], str, set[str]]]]:
    parts, checked = [START, ""], []
    for section in SECTIONS:
        title, sources, lines, derived = section()
        body = "\n".join(lines)
        parts += [f"#### {title}", "", "Manba: " + ", ".join(f"`experiments/results/{s}`" for s in sources), "", body, ""]
        checked.append((title, sources, body, derived))
    parts.append(END)
    return "\n".join(parts), checked


def check(report: Path) -> int:
    text = report.read_text(encoding="utf-8")
    block, sections = render()
    found = re.search(re.escape(START) + r".*?" + re.escape(END), text, re.S)
    if found is None or found.group(0) != block:
        print("report_values: the block differs from what the results give (or is missing)")
        return 1
    total = 0
    for title, sources, body, derived in sections:
        documents = [load(s) for s in sources]
        allowed = set().union(*(allowed_numbers(d) for d in documents)) | derived
        # As tables.verify does: the metrics' own strings (names, statements,
        # labels such as deep_chain) and the folder names are not results.
        stripped = body.replace("95 % CI", " ")
        for s in sources:
            stripped = stripped.replace(s, " ")
        for string in sorted(set().union(*(allowed_strings(d) for d in documents)), key=len, reverse=True):
            stripped = stripped.replace(string, " ")
        tokens = _NUMBER.findall(stripped)
        bad = sorted({t for t in tokens if t not in allowed})
        total += len(tokens)
        if bad:
            print(f"report_values: {title}: numbers not backed by its metrics: {bad}")
            return 1
    print(f"report_values: {total} numbers in {len(sections)} sections checked, 0 differences")
    return 0


def write(report: Path) -> None:
    text = report.read_text(encoding="utf-8")
    block, _ = render()
    found = re.search(re.escape(START) + r".*?" + re.escape(END), text, re.S)
    if found is None:
        raise SystemExit(f"report_values: {report} has no block markers")
    report.write_text(text[:found.start()] + block + text[found.end():], encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m experiments.report_values")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", type=Path)
    mode.add_argument("--check", type=Path)
    args = parser.parse_args(argv)
    if args.write:
        write(args.write)
        return check(args.write)
    return check(args.check)


if __name__ == "__main__":
    sys.exit(main())

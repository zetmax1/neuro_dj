"""
experiments/h2_tuned_tables.py — ``tables.md`` for D73, from the metrics alone.

D48 unchanged: every number here is a scalar already in ``metrics.json``,
rendered by ``tables.fmt``, and ``tables.write`` refuses the file if a token
in it is not. The renderer is passed to ``tables.write`` rather than added to
``experiments/tables.py``, so the renderers behind committed results do not
move.

The table opens with what it is — a post-hoc sensitivity analysis — because a
reader who meets these numbers without that sentence will read them as H2's
verdict, which they are not.
"""

from __future__ import annotations

from experiments.h2_tuned import CONTROL, NEURAL_MODELS
from experiments.tables import _cell, _sources_section, _tree_warning, fmt

MODEL_ORDER: tuple[str, ...] = (CONTROL, *NEURAL_MODELS)


def _auc_cell(entry: dict) -> str:
    """AUC [CI], from the pooled entry's own keys."""
    scores = (entry.get("scores") or {}).get("all") or {}
    auc = scores.get("auc")
    if auc is None:
        return "—"
    interval = entry.get("auc_interval") or {}
    low, high = interval.get("ci_low"), interval.get("ci_high")
    if low is None or high is None:
        return _cell(auc)
    return f"{fmt(auc)} [{fmt(low)}; {fmt(high)}]"


def _difference_cell(item: dict) -> str:
    if item.get("status") != "ok" or item.get("difference") is None:
        return "—"
    return (
        f"{fmt(item['difference'])} "
        f"[{_cell(item.get('ci_low'))}; {_cell(item.get('ci_high'))}]"
    )


def render(metrics: dict) -> str:
    """``tables.md`` for ``python -m experiments.h2_tuned`` (D73)."""
    provenance = metrics.get("provenance", {})
    pooled = metrics.get("pooled") or {}
    models = pooled.get("models") or {}
    training = metrics.get("training") or {}
    reading = metrics.get("reading") or {}
    control = metrics.get("control_check") or {}
    gate = metrics.get("time_gate") or {}
    dataset = metrics.get("dataset") or {}

    lines: list[str] = [
        "# H2 (D73) — neyron modellar to‘liq o‘qitilganda: post-hoc sezgirlik",
        "",
        "Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.",
    ]
    lines += _tree_warning(provenance)
    lines += [
        "",
        "> **Bu H2 ning hukmi emas.** H2 ning hukmi asosiy natijada, natijadan",
        "> oldin belgilangan qoida bo‘yicha chiqarilgan (D56, D59) va bu yerda",
        "> qayta ko‘rilmaydi. Bu jadval bitta savolga javob beradi: neyron",
        "> modellarga to‘liq o‘qitish imkoni berilganda taqqoslash qanday ko‘rinadi.",
        "",
        "Ma’lumot, tozalash, foldlar, seed va D57 baholash tartibi asosiy",
        "natijadagi kodning o‘zi (`h2.prepare`, `h2.fold_sets`, `h2.fit_predict`,",
        "`h2.analyse_pooled`). Faqat giperparametrlar va to‘xtash shartlari boshqa.",
    ]
    if metrics.get("quick"):
        lines += [
            "",
            "> **`--quick` ishga tushirish — dissertatsiya natijasi emas.**",
        ]

    lines += [
        "",
        "## 1. O‘qitish sozlamalari",
        "",
        f"- ko‘pi bilan epoch: {_cell(training.get('epochs_max'))}",
        f"- sabr (patience): {_cell(training.get('patience'))} "
        f"(pyKT ning `train_model` kodida: {_cell(training.get('pykt_patience'))})",
        f"- yaxshilanish chegarasi: {_cell(training.get('this_improvement_threshold'))} "
        f"(pyKT da {_cell(training.get('pykt_improvement_threshold'))} — "
        "kichikroq chegara kechroq to‘xtatadi, ya’ni DKT foydasiga)",
        f"- nomzod tanlanadigan metrika: `{training.get('selected_on', '—')}`",
        f"- DKT to‘ri: {_cell(training.get('grid_dkt_candidates'))} nomzod; "
        f"AKT/AKT-R: {_cell(training.get('grid_attention_candidates'))} nomzod",
        "",
        "## 2. Pooled natija",
        "",
        "| Model | AUC [CI] | RMSE | Aniqlik | Sovuq qatorlar |",
        "|---|---|---|---|---|",
    ]
    for name in MODEL_ORDER:
        entry = models.get(name)
        if entry is None:
            lines.append(f"| {name} | — | — | — | — |")
            continue
        scores = (entry.get("scores") or {}).get("all") or {}
        lines.append(
            f"| {name} | {_auc_cell(entry)} | {_cell(scores.get('rmse'))} "
            f"| {_cell(scores.get('accuracy'))} | {_cell(entry.get('cold_rows'))} |"
        )

    lines += [
        "",
        "## 3. H2 ning farqlari",
        "",
        "Farq — platformaning modeli minus taqqoslanayotgani; oraliq talabalar",
        "bo‘yicha juftlashtirilgan bootstrap.",
        "",
        "| a | b | AUC(a) − AUC(b) [CI] | DeLong p | p (Holm) | Qaror |",
        "|---|---|---|---|---|---|",
    ]
    for item in pooled.get("contrasts", []):
        lines.append(
            f"| {item.get('a', '—')} | {item.get('b', '—')} | {_difference_cell(item)} "
            f"| {_cell(item.get('delong_p'))} | {_cell(item.get('p_holm'))} "
            f"| {item.get('decision', '—')} |"
        )

    lines += [
        "",
        "## 4. Har fold uchun tanlangan kombinatsiya",
        "",
        "Tanlov faqat validatsiya AUC bo‘yicha; sinov qismi tanlash paytida ochilmagan.",
        "",
        "| Fold | Model | Tanlangan | Validatsiya AUC | Epochlar | Nomzodlar |",
        "|---|---|---|---|---|---|",
    ]
    for fold in metrics.get("folds", []):
        for name in NEURAL_MODELS:
            entry = (fold.get("models") or {}).get(name) or {}
            selection = entry.get("selection") or {}
            chosen = selection.get("chosen") or {}
            fit = entry.get("fit") or {}
            lines.append(
                f"| {_cell(fold.get('index'))} | {name} "
                f"| {chosen.get('label', '—')} "
                f"| {_cell(selection.get('validation_auc'))} "
                f"| {_cell(fit.get('epochs_run'))} "
                f"| {_cell(selection.get('candidates'))} |"
            )

    lines += [
        "",
        "## 5. Nazorat va vaqt",
        "",
        f"- nazorat modeli: `{control.get('model', '—')}`, "
        f"pooled AUC {_cell(control.get('auc'))} "
        f"(asosiy natijada {_cell(control.get('reference_auc'))}, "
        f"farq {_cell(control.get('absolute_difference'))}, "
        f"chegara {_cell(control.get('tolerance'))})",
        f"- nazorat mos keldimi: {_cell(control.get('agrees'))}",
        f"- birinchi fold (soniya): {_cell(gate.get('first_fold_seconds'))}, "
        f"bashorat (soat): {_cell(gate.get('projected_hours'))}, "
        f"byudjet (soat): {_cell(gate.get('budget_hours'))}",
        "",
        "## 6. O‘qish qoidasi (D73, natijadan oldin belgilangan)",
        "",
        f"> {reading.get('rule', '—')}",
        "",
        f"- chegara: {_cell(reading.get('floor'))}",
        f"- BKT+IRT − DKT farqining CI pastki chegarasi: {_cell(reading.get('ci_low'))}",
        "",
        f"**Natija: {reading.get('status', '—')}**",
        "",
        reading.get("note", ""),
        "",
        "## 7. Ma’lumot",
        "",
        f"- to‘plam: {dataset.get('label', '—')}",
        f"- talabalar: {_cell(dataset.get('learners_used'))}, "
        f"javoblar: {_cell(dataset.get('answers_used'))}",
        "",
    ]
    lines += _sources_section(metrics, provenance, number=8)
    return "\n".join(lines) + "\n"


__all__ = ["render"]

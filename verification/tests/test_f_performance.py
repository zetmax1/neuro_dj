"""
Group F — V-F1 (query budget, measured here) and V-F2 (the Locust result
against its own ``metrics.json``), plus what D66a's merges must not have broken.

V-F1 is counted independently of ``assessments/tests/test_query_budget.py``:
the reference course of section 4, a real JWT (so the user lookup is counted
as in production), real transactions (``transaction=True``, so ``atomic`` is
not a SAVEPOINT pair), ``CaptureQueriesContext`` on the default connection.

Django 6 records the transaction's BEGIN and COMMIT among the captured
statements; D66 does not count them ("har yozuvchi so'rovda bor"), so they are
set aside here too and the total with them is asserted separately (+2).

The thresholds are soft in the specification ("buzilsa ham FAIL emas"), but
D66a states exact numbers (12 / 12 / 8) and those are what is asserted.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest
from django.conf import settings

from verification.oracle import model as oracle

SEED: int = settings.VERIFICATION_SEED
THESIS = settings.THESIS_MODEL
REPO = Path(settings.BASE_DIR)
LOCUST = REPO / "experiments" / "results" / "locust" / "20261020-100901"

pytestmark = pytest.mark.django_db(transaction=True)


def _user(email):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email=email, password="Verify-F-passw0rd!", first_name="F", last_name="Tekshiruv",
    )


def _jwt_client(user):
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def _questions(course, slugs=("t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"), per_topic=8):
    from assessments.models import Choice, Question

    out = {}
    for slug in slugs:
        out[slug] = []
        for index in range(per_topic):
            question = Question.objects.create(topic_id=course.id_of[slug], text=f"F {slug}-{index}")
            right = Choice.objects.create(question=question, text="right", is_correct=True)
            wrong = Choice.objects.create(question=question, text="wrong", is_correct=False)
            out[slug].append((question, right, wrong))
    return out


def _counted(call):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    with CaptureQueriesContext(connection) as captured:
        response = call()
    return response, [q["sql"] for q in captured.captured_queries]


MARKERS = {"BEGIN", "COMMIT"}


def _work(sql: list[str]) -> list[str]:
    """The statements D66 counts: everything but the transaction's BEGIN/COMMIT."""
    return [statement for statement in sql if statement.strip().upper() not in MARKERS]


def _submit(client, question, choice):
    return client.post(
        "/api/assessments/submit_answer/", {"question_id": question.pk, "choice_id": choice.pk}, format="json",
    )


# ---------------------------------------------------------------------------
# V-F1 — submit_answer, measured here
# ---------------------------------------------------------------------------

def test_v_f1_submit_answer_counts(reference_course):
    from assessments.services.ledger import INSERT_WITH_HISTORY_SQL
    from assessments.services.student_model import WRITE_THETA_AND_B_SQL

    user = _user("v-f1@verify-f.example")
    client = _jwt_client(user)
    questions = _questions(reference_course)
    counts, totals = {}, {}

    # The learner's first request (states are created) — once per learner.
    response, sql = _counted(lambda: _submit(client, *questions["t1"][0][:2]))
    assert response.status_code == 200, response.content[:300]
    counts["first_request"] = len(_work(sql))
    totals["first_request"] = len(sql)

    # An ordinary answer: wrong, so M stays 0.
    question, right, wrong = questions["t1"][1]
    response, sql = _counted(lambda: _submit(client, question, wrong))
    assert response.status_code == 200 and response.json()["status"] != "mastered"
    counts["ordinary"] = len(_work(sql))
    totals["ordinary"] = len(sql)
    joined = "\n".join(sql)
    # D66a's two literal statements are what ran (whitespace aside).
    for statement in (WRITE_THETA_AND_B_SQL, INSERT_WITH_HISTORY_SQL):
        head = " ".join(statement.split())[:60]
        assert head in " ".join(joined.split()), head

    # The same question again inside the window: review_repeat.
    response, sql = _counted(lambda: _submit(client, question, right))
    assert response.status_code == 200, response.content[:300]
    counts["review_repeat"] = len(_work(sql))
    totals["review_repeat"] = len(sql)
    from assessments.models import AssessmentAttempt

    assert AssessmentAttempt.objects.filter(user=user).order_by("-id").first().source == "review_repeat"

    # Correct answers on fresh questions until M flips (t1 → t3 opens).
    for question, right, _ in questions["t1"][2:]:
        response, sql = _counted(lambda: _submit(client, question, right))
        assert response.status_code == 200, response.content[:300]
        if response.json()["status"] == "mastered":
            counts["m_changes"] = len(_work(sql))
            totals["m_changes"] = len(sql)
            assert response.json()["opened_topics"], "M flipped but nothing opened"
            break
    else:
        raise AssertionError("t1 never reached M = 1")

    assert counts["ordinary"] == 12, counts
    assert counts["m_changes"] == 12, counts
    assert counts["review_repeat"] == 8, counts
    assert counts["first_request"] == 21, counts
    assert all(totals[k] == counts[k] + 2 for k in counts), (counts, totals)


def _extend_course(course, extra: int):
    """``extra`` more topics in a new section, each requiring t8: the graph grows, the learner stays."""
    from curriculum.services import kb

    section = kb.create_node(name="F extra", slug="f-extra", parent=course.id_of["course"], kind="section")
    for index in range(extra):
        topic = kb.create_node(name=f"fx{index}", slug=f"fx{index}", parent=section.pk, kind="topic")
        kb.add_prerequisite(prerequisite=course.id_of["t8"], topic=topic.pk)


@pytest.mark.parametrize("url", ["/api/learning/trajectory/", "/api/curriculum/prerequisite-graph/",
                                 "/api/learning_path/tree/"])
def test_v_f1_the_count_does_not_grow_with_the_number_of_topics(reference_course, url):
    user = _user(f"v-f1-n1{abs(hash(url)) % 1000}@verify-f.example")
    client = _jwt_client(user)
    client.get(url)  # states and snapshot
    response, small = _counted(lambda: client.get(url))
    assert response.status_code == 200, response.content[:300]

    _extend_course(reference_course, 30)
    client.get(url)  # TY6 resync after the KB version moved, and a fresh snapshot
    response, large = _counted(lambda: client.get(url))
    assert response.status_code == 200, response.content[:300]
    assert len(_work(large)) == len(_work(small)), (url, len(small), len(large))


# ---------------------------------------------------------------------------
# D66a did not change a single value: random answers against the oracle
# ---------------------------------------------------------------------------

def _constants() -> dict:
    return dict(
        g_max=THESIS["G_MAX"], s_max=THESIS["S_MAX"], a_q=THESIS["A_Q"],
        elo_alpha=THESIS["ELO_ALPHA"], elo_beta=THESIS["ELO_BETA"],
        lam=THESIS["LAMBDA"], cap=THESIS["TAU"] - THESIS["C_OFFSET"], theta_clamp=THESIS["THETA_CLAMP"],
    )


def _params() -> dict:
    return dict(p0=THESIS["DEFAULT_P0"], pt=THESIS["DEFAULT_PT"],
                g0=THESIS["DEFAULT_G0"], s0=THESIS["DEFAULT_S0"])


def test_d66a_random_answers_replay_through_the_oracle(reference_course, snapshot_now):
    """
    Three learners, random open topics, random questions (repeats included) and
    random correctness, all through the API. Every non-repeat ledger row is then
    replayed with ``verification.oracle.model.observe`` from the chain of the
    rows before it — P(L) per (learner, topic), θ per learner, b and n per
    question across learners, P(L0) from the learner's P(L) on Pre(w) in G_L —
    and must match to 1e-9.
    """
    from assessments.models import AssessmentAttempt, Question

    rng = random.Random(SEED + 66)
    questions = _questions(reference_course, per_topic=12)
    by_topic = {reference_course.id_of[s]: v for s, v in questions.items()}
    learners = [_user(f"v-f-oracle{i}@verify-f.example") for i in range(3)]
    clients = {u.pk: _jwt_client(u) for u in learners}
    initial_b = {q.pk: q.irt_difficulty for rows in questions.values() for q, _r, _w in rows}

    asked: set[tuple[int, int]] = set()
    for _ in range(150):
        user = rng.choice(learners)
        states = clients[user.pk].get("/api/knowledge_states/").json()
        rows = states["results"] if isinstance(states, dict) and "results" in states else states
        open_topics = [r["topic"] for r in rows if r["status"] != "closed" and r["topic"] in by_topic]
        pool = by_topic[rng.choice(open_topics)]
        fresh = [q for q in pool if (user.pk, q[0].pk) not in asked]
        # mostly a question the learner has not seen; sometimes a repeat (review_repeat)
        question, right, wrong = rng.choice(fresh if fresh and rng.random() < 0.9 else pool)
        asked.add((user.pk, question.pk))
        response = _submit(clients[user.pk], question, right if rng.random() < 0.7 else wrong)
        assert response.status_code == 200, response.content[:300]

    edges = snapshot_now().edges
    pre = {}
    for (a, b), edge in edges.items():
        pre.setdefault(b, []).append((a, getattr(edge, "weight", edge)))
    params, constants = _params(), _constants()

    p_l, theta, n_student, b, n_question = {}, {}, {}, dict(initial_b), {}
    replayed = repeats = 0
    for row in AssessmentAttempt.objects.order_by("id"):
        if row.source == "review_repeat":
            assert row.p_before is None and row.p_after is None
            repeats += 1
            continue
        key = (row.user_id, row.topic_id)
        if key in p_l:
            assert row.p_before == pytest.approx(p_l[key], abs=1e-12)
        else:
            prerequisites = tuple(
                oracle.Pre(weight=w, p_l=p_l.get((row.user_id, a)), p0=params["p0"]) for a, w in pre.get(row.topic_id, ())
            )
            assert row.p_before == pytest.approx(oracle.initial_mastery(
                p0=params["p0"], prerequisites=prerequisites, lam=constants["lam"], cap=constants["cap"]), abs=1e-12)
        is_correct = row.selected_choice.is_correct
        step = oracle.observe(
            **params, **constants, is_correct=is_correct, p_l=row.p_before,
            theta=theta.get(row.user_id, 0.0), b_q=b[row.question_id],
            n_student=n_student.get(row.user_id, 0), n_question=n_question.get(row.question_id, 0),
        )
        for name, mine, theirs in (
            ("theta_before", row.theta_before, theta.get(row.user_id, 0.0)),
            ("b_before", row.b_before, b[row.question_id]),
            ("p_hat", row.p_hat, step.p_hat), ("p_after", row.p_after, step.p_after),
            ("guess", row.guess_used, step.guess), ("slip", row.slip_used, step.slip),
            ("theta_after", row.theta_after, step.theta_after), ("b_after", row.b_after, step.b_after),
        ):
            assert mine == pytest.approx(theirs, abs=1e-9), (row.pk, name, mine, theirs)
        p_l[key] = step.p_after
        theta[row.user_id] = step.theta_after
        n_student[row.user_id] = n_student.get(row.user_id, 0) + 1
        b[row.question_id] = step.b_after
        n_question[row.question_id] = n_question.get(row.question_id, 0) + 1
        replayed += 1

    assert replayed >= 100 and repeats >= 1, (replayed, repeats)
    for question in Question.objects.filter(pk__in=b):
        assert question.irt_difficulty == pytest.approx(b[question.pk], abs=1e-9)
        assert question.n_answers == n_question.get(question.pk, 0)


# ---------------------------------------------------------------------------
# V-F2 — the committed Locust result, read against its metrics
# ---------------------------------------------------------------------------

def _locust():
    if not LOCUST.exists():
        pytest.skip(f"natija yo'q: {LOCUST}")
    return (json.loads((LOCUST / "metrics.json").read_text(encoding="utf-8")),
            (LOCUST / "tables.md").read_text(encoding="utf-8"))


def _shown(token: str, value) -> bool:
    places = len(token.split(".")[1]) if "." in token else 0
    return round(float(value), places) == float(token)


def test_v_f2_the_locust_table_is_its_metrics():
    from experiments import tables

    metrics, text = _locust()
    assert tables.verify(text, metrics) == []
    rows = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells[0] in metrics["endpoints"] | {"Aggregated": None}:
            rows[cells[0]] = cells
    for name in ("next_question", "submit_answer", "trajectory", "Aggregated"):
        entry = metrics["endpoints"][name]
        requests, failures, share, p50, p95, rps = rows[name][1:7]
        assert int(requests) == entry["requests"] and int(failures) == entry["failures"], name
        assert _shown(share, entry["error_share"]) and _shown(rps, entry["rps"]), name
        assert float(p50) == entry["p50_ms"] and float(p95) == entry["p95_ms"], name
    for name in ("next_question", "submit_answer", "trajectory"):
        assert metrics["endpoints"][name]["p95_ms"] < metrics["v_f2_target_ms"] == 300
        assert metrics["endpoints"][name]["failures"] == 0
    run = metrics["run"]
    assert (run["users"], run["duration_s"], run["server_kind"], run["workers"], run["debug"]) == (
        50, 120, "gunicorn", 8, False)
    assert (run["course"]["topics"], run["course"]["prerequisites"]) == (500, 1500)


def test_v_f2_the_report_quotes_the_same_numbers():
    """REMEDIATION_REPORT §6 and THESIS_MAPPING 10.2 name the same p95 values as the metrics."""
    metrics, _ = _locust()
    report = (REPO / "REMEDIATION_REPORT.md").read_text(encoding="utf-8")
    mapping = (REPO / "docs" / "THESIS_MAPPING.md").read_text(encoding="utf-8")
    e = metrics["endpoints"]
    for name in ("next_question", "submit_answer", "trajectory"):
        row = f"| {name} | {e[name]['requests']} | 0 | {e[name]['p50_ms']:.0f} | {e[name]['p95_ms']:.0f} |"
        assert row in report, row
    trio = f"p95 {e['next_question']['p95_ms']:.0f} / {e['submit_answer']['p95_ms']:.0f} / {e['trajectory']['p95_ms']:.0f} ms"
    assert trio in mapping, trio

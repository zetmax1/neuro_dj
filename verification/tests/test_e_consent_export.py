"""
V-E1, V-E2 — the consent and export part of group E (D42-D46, D11), D47.

Written from ``NEUROLEARN_VERIFICATION.md`` (V-E1, V-E2), ``NEUROLEARN_B8_PLAN.md``
section 3 (D42-D45) and ``NEUROLEARN_B8B.md`` (D46), without reading the
implementer's tests. The prototype is driven the way a learner drives it:
consent is given and withdrawn through ``/api/me/consent/`` and registration,
answers are submitted through ``/api/assessments/submit_answer/``, the export is
the real management command and the retention is the real Celery task.

The rows the export must leave out are planted so that they differ from an
exported row in **one** property only (the source, the topic being archived,
the account being simulated, the consent): a filter that keys on anything else
would let them through and the test would see it.
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

import pytest
from django.core.management import call_command
from django.utils import timezone

pytestmark = pytest.mark.django_db

FILES = ("pykt_sequences.txt", "attempts.csv", "knowledge_base.json", "metadata.json")
PASSWORD = "Verify-E-pass-2026!"
HEX16 = re.compile(r"^[0-9a-f]{16}$")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _client(user=None):
    from rest_framework.test import APIClient

    client = APIClient()
    if user is not None:
        client.force_authenticate(user=user)
    return client


def _user(email, first, last, **extra):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create_user(
        email=email, password=PASSWORD, first_name=first, last_name=last, **extra
    )


def _question(topic_id: int, label: str):
    from assessments.models import Choice, Question

    question = Question.objects.create(topic_id=topic_id, text=f"V-E question {label}")
    right = Choice.objects.create(question=question, text="right", is_correct=True)
    wrong = Choice.objects.create(question=question, text="wrong", is_correct=False)
    return question, right, wrong


def _answer(user, question, choice):
    response = _client(user).post(
        "/api/assessments/submit_answer/",
        {"question_id": question.pk, "choice_id": choice.pk},
        format="json",
    )
    assert response.status_code == 200, (response.status_code, response.content[:300])
    from assessments.models import AssessmentAttempt

    return AssessmentAttempt.objects.filter(user=user).order_by("-id").first()


def _set_consent(user, value: bool):
    response = _client(user).patch("/api/me/consent/", {"research_consent": value}, format="json")
    assert response.status_code == 200, response.content
    user.refresh_from_db()
    assert user.research_consent is value


def _export(out: Path | None = None, **options) -> tuple[Path | None, str]:
    stdout, stderr = io.StringIO(), io.StringIO()
    if out is not None:
        options["out"] = str(out)
    call_command("export_research_data", stdout=stdout, stderr=stderr, **options)
    return out, stdout.getvalue() + stderr.getvalue()


def _read(directory: Path) -> dict[str, str]:
    return {name: (directory / name).read_text(encoding="utf-8") for name in FILES}


def _csv_rows(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


# One learner's block as pyKT 0.0.38 reads it (``pykt/preprocess/split_datasets.py:9-79``,
# ``read_data`` walks the file in steps of ``i % 6``). A line holding "NA" is an
# absent column; responses are always read.
PYKT_BLOCK = ("uid,seq_len", "questions", "concepts", "responses", "timestamps", "usetimes")


def _pykt_blocks(text: str) -> list[list[str]]:
    lines = text.splitlines()
    size = len(PYKT_BLOCK)
    assert len(lines) % size == 0, f"a pyKT block is {size} lines"
    return [lines[i:i + size] for i in range(0, len(lines), size)]


def _json_keys(value, out=None) -> set[str]:
    out = set() if out is None else out
    if isinstance(value, dict):
        for key, item in value.items():
            out.add(str(key))
            _json_keys(item, out)
    elif isinstance(value, list):
        for item in value:
            _json_keys(item, out)
    return out


def _key(row) -> tuple[str, int, int]:
    """An exported row's identity: (pseudonym, topic, attempt_no) is unique (D10)."""
    return (row.user.research_pseudonym, row.topic_id, row.attempt_no)


def _csv_key(row: dict[str, str]) -> tuple[str, int, int]:
    return (row["pseudonym"], int(row["topic_id"]), int(row["attempt_no"]))


# ---------------------------------------------------------------------------
# the world: learners, answers, planted rows
# ---------------------------------------------------------------------------

@dataclass
class World:
    users: dict[str, object]
    # Everything identifying that was ever stored, captured before any
    # anonymisation could overwrite it.
    identities: list[tuple[str, str, str]]
    planted: dict[str, tuple[str, int, int]] = field(default_factory=dict)
    archived_topic: int = 0
    expected: set[tuple[str, int, int]] = field(default_factory=set)


@pytest.fixture
def world(reference_course) -> World:
    from django.db import transaction

    from assessments.models import AssessmentAttempt, AttemptSource
    from assessments.services.ledger import ModelTrace, record_attempt
    from assessments.services.orchestrator import process_submission
    from curriculum.services import kb

    course = reference_course
    t1, t2 = course.id_of["t1"], course.id_of["t2"]
    # A leaf with no prerequisite, so it is open; it is archived after use.
    tx = kb.create_node(name="Arxivlanadigan", slug="v-e-tx", parent=course.id_of["B1"], kind="topic").pk

    q1, q1_right, q1_wrong = _question(t1, "1")
    q2, q2_right, _ = _question(t1, "2")
    q3, _, q3_wrong = _question(t2, "3")
    qx, qx_right, _ = _question(tx, "x")

    users = {
        "alice": _user("alice.qodirova.v47@verify-e.example", "Aliyaxon", "Qodirovaeva"),
        "bob": _user("bob.toshmatov.v47@verify-e.example", "Bobomurod", "Toshmatovich"),
        "carol": _user("carol.rahimova.v47@verify-e.example", "Karolinaxon", "Rahimovaeva"),
        "sim": _user("sim.learner.v47@simulated.invalid", "Simulyatsiya", "Talabasi", is_simulated=True),
        "admin": _user("root.admin.v47@verify-e.example", "Administratorbek", "Bosh", is_staff=True,
                       is_superuser=True),
    }

    # Erin consents at registration, through the public endpoint.
    response = _client().post("/api/accounts/register/", {
        "email": "erin.yusupova.v47@verify-e.example",
        "password": PASSWORD, "password_confirm": PASSWORD,
        "first_name": "Erkinoyxon", "last_name": "Yusupovaeva",
        "research_consent": True,
    }, format="json")
    assert response.status_code in (200, 201), response.content
    from django.contrib.auth import get_user_model

    users["erin"] = get_user_model().objects.get(email="erin.yusupova.v47@verify-e.example")
    assert users["erin"].research_consent is True

    identities = [(u.email, u.first_name, u.last_name) for u in users.values()]

    _set_consent(users["alice"], True)
    _set_consent(users["carol"], True)
    users["sim"].research_consent = True  # consenting, but simulated (D13)
    users["sim"].save(update_fields=["research_consent"])

    alice, erin = users["alice"], users["erin"]
    w = World(users=users, identities=identities)

    # Real observations that must be exported.
    real = [
        _answer(alice, q1, q1_right),
        _answer(alice, q2, q2_right),
        _answer(alice, q3, q3_wrong),
        _answer(erin, q1, q1_wrong),
        _answer(erin, q3, q3_wrong),
    ]
    for row in real:
        assert row.source == AttemptSource.ADAPTIVE
    w.expected = {_key(row) for row in real}
    engine = real[0].engine_version
    assert engine.startswith("thesis_hybrid"), engine

    # review_repeat: the same question again inside the window (D25), via the API.
    repeat = _answer(alice, q1, q1_wrong)
    assert repeat.source == AttemptSource.REVIEW_REPEAT, repeat.source
    w.planted["review_repeat"] = _key(repeat)

    # seed / simulated / legacy on the consenting learner, with the same engine
    # version as her real rows: only the source differs.
    with transaction.atomic():
        seed = record_attempt(user=alice, choice=q2_right, source=AttemptSource.SEED,
                              trace=ModelTrace(engine_version=engine))
        simulated = record_attempt(user=alice, choice=q2_right, source=AttemptSource.SIMULATED,
                                   trace=ModelTrace(engine_version=engine))
        last = AssessmentAttempt.objects.filter(user=alice, topic_id=t1).order_by("-attempt_no").first()
        legacy = AssessmentAttempt.objects.create(
            user=alice, question=q1, selected_choice=q1_right, is_correct=True,
            topic_id=t1, course_id=last.course_id, attempt_no=last.attempt_no + 1,
            source=AttemptSource.LEGACY, engine_version=engine, kb_version=last.kb_version,
        )
    w.planted.update(seed=_key(seed), simulated=_key(simulated), legacy=_key(legacy))

    # Archived topic: a real adaptive answer, then the topic is archived.
    archived = _answer(alice, qx, qx_right)
    assert archived.source == AttemptSource.ADAPTIVE
    kb.archive_node(tx)
    w.planted["archived_topic"] = _key(archived)
    w.archived_topic = tx

    # No consent / withdrawn consent: real adaptive answers.
    w.planted["no_consent"] = _key(_answer(users["bob"], q1, q1_right))
    carol_row = _answer(users["carol"], q1, q1_right)  # given while consenting...
    _set_consent(users["carol"], False)                 # ...then withdrawn
    assert users["carol"].research_consent_at is not None
    w.planted["withdrawn"] = _key(carol_row)

    # Simulated account: an adaptive answer through the API and an answer the
    # way the simulator writes them (process_submission, source=simulated).
    w.planted["simulated_account_adaptive"] = _key(_answer(users["sim"], q3, q3_wrong))
    with transaction.atomic():
        process_submission(user=users["sim"], question_id=q1.pk, choice_id=q1_right.pk,
                           source=AttemptSource.SIMULATED)
    sim_row = AssessmentAttempt.objects.filter(user=users["sim"]).order_by("-id").first()
    assert sim_row.source == AttemptSource.SIMULATED
    w.planted["simulated_account_simulator"] = _key(sim_row)
    return w


@pytest.fixture
def exported(world, tmp_path) -> dict[str, str]:
    out, _ = _export(tmp_path / "export")
    return _read(out)


# ---------------------------------------------------------------------------
# V-E1 — no email, no name, no user_id; only the pseudonym
# ---------------------------------------------------------------------------

def test_v_e1_no_email_or_name_in_any_of_the_four_files(world, exported):
    for name, text in exported.items():
        lowered = text.lower()
        for email, first, last in world.identities:
            assert email.lower() not in lowered, f"{email} in {name}"
            assert email.split("@")[0].lower() not in lowered, f"local part of {email} in {name}"
            for part in (first, last):
                assert part.lower() not in lowered, f"name {part!r} in {name}"
        assert "@" not in text, f"an email-like token in {name}"


def test_v_e1_no_user_id_column_key_or_disguised_column(world, exported):
    from django.contrib.auth import get_user_model

    rows = _csv_rows(exported["attempts.csv"])
    assert rows, "the export is empty"
    header = list(rows[0])
    bad = [c for c in header if re.search(r"user|email|name|^id$", c, re.I)]
    assert bad == [], f"identifying columns in attempts.csv: {bad}"

    # No column is the user id under another name: for every column, check
    # whether it equals the row's internal user id on every row.
    pk_of = {u.research_pseudonym: u.pk for u in get_user_model().all_objects.all()}
    assert len({pk_of[r["pseudonym"]] for r in rows}) >= 2, "need two learners to tell ids apart"
    for column in header:
        if all(r[column] == str(pk_of[r["pseudonym"]]) for r in rows):
            pytest.fail(f"column {column!r} carries the internal user id")

    for name in ("knowledge_base.json", "metadata.json"):
        keys = _json_keys(json.loads(exported[name]))
        bad = sorted(k for k in keys if re.search(r"user|e-?mail|first_name|last_name|full_name", k, re.I))
        assert bad == [], f"identifying keys in {name}: {bad}"


def test_v_e1_the_only_learner_identifier_is_the_pseudonym(world, exported):
    from django.contrib.auth import get_user_model

    users = {u.research_pseudonym: u for u in get_user_model().all_objects.all()}
    pks = {str(u.pk) for u in users.values()}

    rows = _csv_rows(exported["attempts.csv"])
    for row in rows:
        assert row["pseudonym"] in users and HEX16.match(row["pseudonym"])
    for block in _pykt_blocks(exported["pykt_sequences.txt"]):
        learner = block[0].split(",")[0]
        assert learner in users, f"pyKT block header {learner!r} is not a pseudonym"
        assert learner not in pks


# ---------------------------------------------------------------------------
# V-E2 — who and what is left out
# ---------------------------------------------------------------------------

def test_v_e2_exactly_the_real_consenting_rows_are_exported(world, exported):
    got = {_csv_key(r) for r in _csv_rows(exported["attempts.csv"])}
    assert got == world.expected, (
        f"missing {sorted(world.expected - got)}, unexpected {sorted(got - world.expected)}"
    )


@pytest.mark.parametrize("what", [
    "no_consent", "withdrawn", "review_repeat", "seed", "simulated", "legacy",
    "archived_topic", "simulated_account_adaptive", "simulated_account_simulator",
])
def test_v_e2_a_planted_row_is_not_exported(world, exported, what):
    got = {_csv_key(r) for r in _csv_rows(exported["attempts.csv"])}
    assert world.planted[what] not in got, f"{what} row {world.planted[what]} was exported"


def test_v_e2_non_consenting_withdrawn_and_simulated_learners_appear_nowhere(world, exported):
    for who in ("bob", "carol", "sim", "admin"):
        pseudonym = world.users[who].research_pseudonym
        for name, text in exported.items():
            assert pseudonym not in text, f"{who}'s pseudonym in {name}"


def test_v_e2_sources_and_archived_topic_in_every_file(world, exported):
    rows = _csv_rows(exported["attempts.csv"])
    assert {r["source"] for r in rows} <= {"adaptive", "test_session"}
    assert all(int(r["topic_id"]) != world.archived_topic for r in rows)

    for block in _pykt_blocks(exported["pykt_sequences.txt"]):
        assert str(world.archived_topic) not in block[2].split(",")

    graph = json.loads(exported["knowledge_base.json"])
    assert world.archived_topic not in {node["id"] for node in graph["nodes"]}


def test_v_e2_counts_agree_across_the_files(world, exported):
    """V-E3 (row counts part): metadata, CSV and pyKT describe the same rows."""
    meta = json.loads(exported["metadata.json"])
    rows = _csv_rows(exported["attempts.csv"])
    blocks = _pykt_blocks(exported["pykt_sequences.txt"])
    assert meta["counts"]["rows"] == len(rows) == sum(int(b[0].split(",")[1]) for b in blocks)
    assert meta["counts"]["learners"] == len(blocks) == len({r["pseudonym"] for r in rows})
    for block in blocks:
        n = int(block[0].split(",")[1])
        # questions, concepts, responses, timestamps: one value per answer, and
        # none that pyKT would take for an absent column.
        assert all(len(line.split(",")) == n and "NA" not in line for line in block[1:5])
        # usetimes: the platform records no answer duration, so pyKT's "NA".
        assert block[5] == "NA" or len(block[5].split(",")) == n, block[5]
    # bob and carol are the two real learners left out for consent (D45).
    assert meta["counts"]["excluded_no_consent_learners"] == 2
    assert meta["thesis_result"] is True


# ---------------------------------------------------------------------------
# --include-simulated is marked in three places (D44, D13)
# ---------------------------------------------------------------------------

def test_v_e2_include_simulated_warns_flags_and_names_the_directory(world, tmp_path, settings):
    settings.BASE_DIR = tmp_path  # the default directory is <BASE_DIR>/exports/
    _, plain_log = _export()
    _, sim_log = _export(include_simulated=True)

    made = sorted((tmp_path / "exports").iterdir())
    assert len(made) == 2
    plain = [d for d in made if "simulated" not in d.name]
    marked = [d for d in made if d.name.endswith("-simulated")]
    assert len(plain) == 1 and len(marked) == 1, [d.name for d in made]

    # The plain run lists "simulated" among the excluded sources; what it must
    # not print is the warning.
    assert not re.search(r"not a thesis result|include-simulated", plain_log), plain_log
    assert re.search(r"simulat", sim_log, re.I) and re.search(r"not a thesis result|D13", sim_log), sim_log

    assert json.loads((plain[0] / "metadata.json").read_text())["thesis_result"] is True
    assert json.loads((marked[0] / "metadata.json").read_text())["thesis_result"] is False


def test_v_e2_include_simulated_exports_what_the_simulator_wrote(world, tmp_path):
    """
    D44: ``--include-simulated`` "simulyatsiya hisoblarini roziligidan qat'i nazar
    kiritadi" — it exists to test the pipeline on simulator data. The simulator
    (``simulate_bkt_data``) writes every answer with ``source=simulated``, so
    the simulator's own rows must be in such an export.
    """
    _export(tmp_path / "sim", include_simulated=True)
    # D44 marks the directory even when --out names it, so the export of
    # ``tmp/sim`` lands in ``tmp/sim-simulated``; reading ``tmp/sim`` was this
    # test's own mistake and made it contradict
    # ``…_with_an_explicit_out_still_marks_the_directory`` (R2, 2026-10-05).
    written = [p for p in tmp_path.iterdir() if (p / "metadata.json").exists()]
    assert [p.name for p in written] == ["sim-simulated"], [p.name for p in tmp_path.iterdir()]
    assert not (tmp_path / "sim").exists()
    out = written[0]

    got = {_csv_key(r) for r in _csv_rows((out / "attempts.csv").read_text(encoding="utf-8"))}
    assert world.planted["simulated_account_simulator"] in got, (
        "--include-simulated left out every row the simulator wrote: the export "
        "filters source IN (adaptive, test_session) before the simulated accounts "
        "are added, and the simulator writes source=simulated"
    )
    # the real learner's own ``simulated`` row stays out: the flag widens the
    # export to simulator *accounts*, not to simulated rows of real accounts
    assert world.planted["simulated"] not in got


def test_v_e2_include_simulated_on_simulator_only_data_is_not_empty(reference_course, tmp_path):
    """
    The pipeline test D44 describes, end to end: a database with simulator
    accounts only, then ``--include-simulated``.
    """
    from django.db import transaction

    from assessments.models import AttemptSource
    from assessments.services.orchestrator import process_submission

    sim = _user("only.sim.v47@simulated.invalid", "Sim", "Only", is_simulated=True)
    q, right, wrong = _question(reference_course.id_of["t1"], "s")
    with transaction.atomic():
        for choice in (right, wrong, right):
            process_submission(user=sim, question_id=q.pk, choice_id=choice.pk,
                               source=AttemptSource.SIMULATED)
    _, log = _export(dry_run=True, include_simulated=True)
    match = re.search(r"Exported:\s+(\d+) answer", log)
    assert match, log
    assert int(match.group(1)) == 3, f"--include-simulated exported {match.group(1)} of 3 simulator answers:\n{log}"


def test_v_e2_include_simulated_with_an_explicit_out_still_marks_the_directory(world, tmp_path):
    """
    D44: "papka nomiga ``-simulated`` qo'shiladi". With ``--out`` the directory
    is taken verbatim, so a simulated export can sit under a thesis-looking
    name; only ``metadata.json`` still says ``thesis_result: false``.
    """
    target = tmp_path / "research-final"
    _export(target, include_simulated=True)
    written = [p for p in tmp_path.iterdir() if (p / "metadata.json").exists()]
    assert written, "nothing was written"
    assert all("simulated" in p.name for p in written), [p.name for p in written]


# ---------------------------------------------------------------------------
# the pseudonym (D43)
# ---------------------------------------------------------------------------

def test_v_e1_pseudonym_is_not_a_function_of_id_email_or_name(db):
    """
    Same primary key, same email, same names — a new row. A pseudonym derived
    from any of them (hashed, salted with a constant, anything deterministic)
    would come back identical.
    """
    first = _user("same.person.v47@verify-e.example", "Bir", "Xil")
    pk, before = first.pk, first.research_pseudonym
    first.hard_delete()
    again = _user("same.person.v47@verify-e.example", "Bir", "Xil", pk=pk)
    assert again.pk == pk
    assert HEX16.match(before) and HEX16.match(again.research_pseudonym)
    assert again.research_pseudonym != before


def test_v_e1_pseudonym_is_not_a_plain_hash_and_is_unique(db):
    import hashlib

    users = [_user(f"learner{i}.v47@verify-e.example", f"Ism{i}", f"Fam{i}") for i in range(60)]
    assert len({u.research_pseudonym for u in users}) == len(users)
    for u in users:
        sources = [str(u.pk), u.email, u.email.lower(), f"{u.pk}{u.email}", f"{u.first_name} {u.last_name}"]
        for source in sources:
            for algo in ("md5", "sha1", "sha256", "sha512", "blake2b", "sha3_256"):
                digest = hashlib.new(algo, source.encode()).hexdigest()
                assert u.research_pseudonym not in digest, (algo, source)


def test_v_e1_pseudonym_is_in_no_api_response(world):
    """
    Every argument-free GET route of the API, as the learner and as an admin,
    plus the routes that take a user or topic id, and the POST/PATCH responses
    a learner sees. None may contain a pseudonym.
    """
    from django.urls import URLPattern, URLResolver, get_resolver

    def walk(patterns, prefix=""):
        for p in patterns:
            route = prefix + str(p.pattern)
            if isinstance(p, URLResolver):
                yield from walk(p.url_patterns, route)
            elif isinstance(p, URLPattern):
                yield route

    routes = sorted({r.lstrip("^").rstrip("$") for r in walk(get_resolver().url_patterns)})
    plain = [r for r in routes if r.startswith("api/") and "<" not in r and "(" not in r and "\\" not in r]
    assert len(plain) > 10, plain

    alice, admin = world.users["alice"], world.users["admin"]
    t1 = sorted(world.expected)[0][1]
    extra = [
        f"api/accounts/users/{alice.pk}/",
        f"api/learning/path-to/{t1}/",
        f"api/learning/topics/{t1}/history/",
        f"api/assessments/next_question/?topic_id={t1}",
        "api/accounts/users/?consent=true",
    ]
    secrets = {u.research_pseudonym for u in world.users.values()}
    checked = 0
    for who in (alice, admin):
        client = _client(who)
        client.raise_request_exception = False
        for route in plain + extra:
            response = client.get("/" + route)
            body = b"".join(response) if getattr(response, "streaming", False) else response.content
            text = body.decode("utf-8", "replace")
            for secret in secrets:
                assert secret not in text, f"pseudonym in GET /{route} as {who.email}"
            checked += 1

    responses = [
        _client(alice).patch("/api/me/consent/", {"research_consent": True}, format="json"),
        _client(alice).patch("/api/accounts/profile/", {"first_name": "Aliyaxon"}, format="json"),
        _client().post("/api/accounts/register/", {
            "email": "frank.v47@verify-e.example", "password": PASSWORD,
            "password_confirm": PASSWORD, "research_consent": True}, format="json"),
    ]
    from django.contrib.auth import get_user_model

    secrets.add(get_user_model().objects.get(email="frank.v47@verify-e.example").research_pseudonym)
    for response in responses:
        assert response.status_code in (200, 201), response.content
        for secret in secrets:
            assert secret not in response.content.decode()
    assert checked > 20


# ---------------------------------------------------------------------------
# an admin cannot change somebody else's consent (D42)
# ---------------------------------------------------------------------------

def _consent_state(user):
    user.refresh_from_db()
    return user.research_consent, user.research_consent_at


def test_v_e2_admin_cannot_change_consent_through_the_api(world):
    admin, bob, alice = world.users["admin"], world.users["bob"], world.users["alice"]
    bob_before, alice_before = _consent_state(bob), _consent_state(alice)
    client = _client(admin)

    client.patch(f"/api/accounts/users/{bob.pk}/",
                 {"research_consent": True, "research_consent_at": "2026-01-01T00:00:00Z"}, format="json")
    client.patch(f"/api/accounts/users/{alice.pk}/", {"research_consent": False}, format="json")
    for method in ("put", "post"):
        response = getattr(client, method)(f"/api/accounts/users/{bob.pk}/",
                                           {"research_consent": True}, format="json")
        assert response.status_code == 405
    # The consent endpoint addresses the caller only, whatever the body says.
    client.patch("/api/me/consent/",
                 {"research_consent": True, "user": bob.pk, "user_id": bob.pk, "id": bob.pk,
                  "email": bob.email}, format="json")

    assert _consent_state(bob) == bob_before
    assert _consent_state(alice) == alice_before


def test_v_e2_admin_cannot_change_consent_through_django_admin(world):
    from django.contrib import admin as django_admin
    from django.contrib.auth import get_user_model
    from django.test import Client, RequestFactory

    User = get_user_model()
    root, bob = world.users["admin"], world.users["bob"]
    model_admin = django_admin.site._registry[User]
    request = RequestFactory().get("/")
    request.user = root
    form = model_admin.get_form(request, obj=bob)
    assert "research_consent" not in form.base_fields
    assert "research_consent_at" not in form.base_fields
    assert "research_pseudonym" not in form.base_fields

    client = Client()
    client.force_login(root)
    page = client.get(f"/admin/accounts/customuser/{bob.pk}/change/")
    assert page.status_code == 200
    html = page.content.decode()
    assert 'name="research_consent"' not in html
    assert bob.research_pseudonym not in html

    before = _consent_state(bob)
    client.post(f"/admin/accounts/customuser/{bob.pk}/change/", {
        "email": bob.email, "first_name": bob.first_name, "last_name": bob.last_name,
        "is_active": "on", "research_consent": "on",
        "research_consent_at_0": "2026-01-01", "research_consent_at_1": "00:00:00",
        "_save": "Save",
    })
    assert _consent_state(bob) == before


# ---------------------------------------------------------------------------
# D46 — the consent text says what deleting the account does (uz and en)
# ---------------------------------------------------------------------------

FRONTEND = Path.home() / "Desktop" / "neuro" / "neuro"


def test_d46_consent_text_says_answers_are_kept_after_account_deletion():
    locales = FRONTEND / "src" / "locales"
    if not locales.exists():
        pytest.skip(f"frontend checkout not found at {FRONTEND}")
    texts = {
        lang: json.loads((locales / f"{lang}.json").read_text(encoding="utf-8"))["consent"]
        for lang in ("uz", "en")
    }
    # The sixth fact, in the words of D46.
    uz = " ".join(texts["uz"].values())
    assert "hisobingizni o‘chirsangiz" in uz or "hisobingizni o'chirsangiz" in uz
    assert "saqlanib qoladi" in uz and "ism va emailsiz" in uz
    assert "avval rozilikni bekor qiling" in uz
    en = " ".join(texts["en"].values()).lower()
    assert "delete your account" in en and "kept" in en
    assert "without your name or email" in en and "withdraw consent first" in en

    # ...and both places that show the consent text render that sentence.
    key = next(k for k, v in texts["en"].items() if "delete your account" in v.lower())
    assert key in texts["uz"]
    for page in ("src/pages/Profile.tsx", "src/pages/Auth.tsx"):
        source = (FRONTEND / page).read_text(encoding="utf-8")
        assert f'"consent.{key}"' in source or f"'consent.{key}'" in source, page


# ---------------------------------------------------------------------------
# D11 — hard delete after 30 days, with and without consent
# ---------------------------------------------------------------------------

def _soft_delete(user, days_ago: float):
    response = _client(user).delete("/api/accounts/profile/")
    assert response.status_code == 204
    from django.contrib.auth import get_user_model

    user = get_user_model().all_objects.get(pk=user.pk)
    user.deleted_at = timezone.now() - timedelta(days=days_ago)
    user.save(update_fields=["deleted_at"])
    return user


def test_d11_retention_with_and_without_consent(world, tmp_path):
    from django.contrib.auth import get_user_model

    from accounts.tasks import gdpr_hard_delete_users
    from assessments.models import AssessmentAttempt

    User = get_user_model()
    alice, bob, carol, erin = (world.users[k] for k in ("alice", "bob", "carol", "erin"))
    alice_identity = (alice.email, alice.first_name, alice.last_name)
    alice_rows = AssessmentAttempt.objects.filter(user=alice).count()
    alice_pseudonym = alice.research_pseudonym

    _soft_delete(alice, 31)   # consent  -> anonymised, answers kept
    _soft_delete(bob, 31)     # never    -> deleted with the answers
    _soft_delete(carol, 31)   # withdrawn -> deleted with the answers
    _soft_delete(erin, 29)    # consent, inside the window -> untouched

    assert gdpr_hard_delete_users() == {"anonymised": 1, "deleted": 2}

    a = User.all_objects.get(pk=alice.pk)
    assert a.research_pseudonym == alice_pseudonym
    assert a.first_name == "" and a.last_name == ""
    assert a.email != alice_identity[0] and alice_identity[0].split("@")[0] not in a.email
    assert not a.has_usable_password() and not a.is_active
    assert AssessmentAttempt.objects.filter(user=a).count() == alice_rows

    for gone in (bob, carol):
        assert not User.all_objects.filter(pk=gone.pk).exists()
        assert not AssessmentAttempt.objects.filter(user_id=gone.pk).exists()

    e = User.all_objects.get(pk=erin.pk)
    assert e.email == erin.email and e.first_name == erin.first_name

    # A second night changes nothing.
    assert gdpr_hard_delete_users() == {"anonymised": 0, "deleted": 0}

    # The anonymised learner is still in the export, under the same pseudonym,
    # and nothing of the old identity is.
    out, _ = _export(tmp_path / "after")
    files = _read(out)
    assert alice_pseudonym in files["attempts.csv"]
    for text in files.values():
        for part in alice_identity:
            assert part.lower() not in text.lower()


# ---------------------------------------------------------------------------
# V-E3 — pyKT's own reader on the exported file (final verification, 2026-10-20)
# ---------------------------------------------------------------------------

PYKT_PYTHON = Path(__file__).resolve().parents[2] / "experiments" / ".venv" / "bin" / "python"
PYKT_READ = """
import json, sys
from pykt.preprocess.split_datasets import read_data
df, keys = read_data(sys.argv[1], min_seq_len=1)
print(json.dumps({"learners": len(df), "uids": sorted(df["uid"]),
                  "interactions": sum(len(r.split(",")) for r in df["responses"]),
                  "keys": sorted(keys)}))
"""


def test_v_e3_pykt_reads_the_exported_sequences_without_error(world, exported, tmp_path):
    """
    V-E3: "pyKT formatidagi fayl pyKT preprocess tomonidan xatosiz o'qiladi,
    qatorlar soni metadata bilan mos keladi". The reader is pykt-toolkit's own
    ``pykt.preprocess.split_datasets.read_data`` (0.0.38, ``experiments/.venv``),
    which takes six lines per learner: uid, questions, concepts, responses,
    timestamps, usetimes ("NA" where absent).
    """
    import subprocess

    if not PYKT_PYTHON.exists():
        pytest.skip(f"experiments/.venv yo'q: {PYKT_PYTHON}")
    path = tmp_path / "pykt_sequences.txt"
    path.write_text(exported["pykt_sequences.txt"], encoding="utf-8")
    done = subprocess.run([str(PYKT_PYTHON), "-I", "-c", PYKT_READ, str(path)], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr[-2000:]
    out = done.stdout.strip().splitlines()
    read = json.loads(out[-1])
    meta = json.loads(exported["metadata.json"])
    pseudonyms = sorted({r["pseudonym"] for r in _csv_rows(exported["attempts.csv"])})
    assert not any("error" in line for line in out[:-1]), out[:-1]
    assert read["uids"] == pseudonyms, read
    assert read["learners"] == meta["counts"]["learners"]
    assert read["interactions"] == meta["counts"]["rows"]

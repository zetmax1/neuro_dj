"""
8a: the research export (D44, D45).

The checks D45 names are the first three below, and they are the ones that
matter: an export file must carry no email, no name and no internal user id; a
learner who did not consent must not be in it; and no ``review_repeat`` row
may be. The rest of the file pins the scope, the counts and the metadata — the
file the thesis points at when asked which data a result came from.
"""

from __future__ import annotations

import csv
import json
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.utils import timezone

from assessments.models import (
    AssessmentAttempt,
    AttemptSource,
    Choice,
    DifficultyLevel,
    Question,
)
from assessments.services.orchestrator import process_submission
from assessments.services.student_model import ENGINE_NAME, ENGINE_VERSION
from curriculum.services import kb
from curriculum.services.graph import clear_local_cache, get_snapshot
from curriculum.testing import make_course, make_section, make_topic

User = get_user_model()

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def course():
    """C ── B (t1, t2), with t1 → t2 so the graph file has an edge to carry."""
    root = make_course("Algoritmlar", slug="ex-course")
    section = make_section("Saralash", root, slug="ex-section", position=0)
    first = make_topic("Pufakli saralash", section, slug="ex-t1", position=0)
    second = make_topic("Tezkor saralash", section, slug="ex-t2", position=1)
    kb.add_prerequisite(prerequisite=first, topic=second, weight=0.8)
    clear_local_cache()
    return {"course": root, "section": section, "t1": first, "t2": second}


def question_on(topic, text="?", b=0.0):
    question = Question.objects.create(
        topic=topic, text=text, difficulty=DifficultyLevel.MEDIUM, irt_difficulty=b,
    )
    right = Choice.objects.create(question=question, text="right", is_correct=True)
    wrong = Choice.objects.create(question=question, text="wrong", is_correct=False)
    return question, right, wrong


def learner(email, *, consent=True, simulated=False, first_name="", last_name=""):
    user = User.objects.create_user(
        email=email, password=None, is_simulated=simulated,
        first_name=first_name, last_name=last_name,
    )
    if consent:
        user.research_consent = True
        user.research_consent_at = timezone.now()
        user.save(update_fields=["research_consent", "research_consent_at"])
    return user


def export(tmp_path, *args, **kwargs):
    """Run the command into a fresh directory and return it with the output."""
    out = tmp_path / kwargs.pop("name", "export")
    buffer = StringIO()
    call_command("export_research_data", "--out", str(out), *args, stdout=buffer, **kwargs)
    return out, buffer.getvalue()


def read_csv(directory):
    with (directory / "attempts.csv").open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(directory, name):
    return json.loads((directory / name).read_text(encoding="utf-8"))


def every_file(directory) -> str:
    """Every byte the export wrote, for the "nothing leaks" checks."""
    return "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(directory.iterdir())
    )


# ---------------------------------------------------------------------------
# The three checks D45 names
# ---------------------------------------------------------------------------

def test_no_email_no_name_and_no_user_id_appear_anywhere(tmp_path, course):
    willing = learner("ali.valiyev@example.org", first_name="Ali", last_name="Valiyev")
    question, right, _ = question_on(course["t1"])
    process_submission(user=willing, question_id=question.pk, choice_id=right.pk)

    directory, _ = export(tmp_path)
    content = every_file(directory)

    assert willing.email not in content
    assert "ali.valiyev" not in content
    assert "Ali" not in content
    assert "Valiyev" not in content
    # The internal id joins to every other table, so publishing it would undo
    # the pseudonym (D43).
    rows = read_csv(directory)
    assert "user_id" not in rows[0]
    assert "pseudonym" in rows[0]
    assert rows[0]["pseudonym"] == willing.research_pseudonym
    assert json.dumps(read_json(directory, "metadata.json"))
    for name in ("email", "first_name", "last_name", "user_id"):
        assert name not in read_csv(directory)[0]


def test_a_learner_without_consent_is_not_in_the_export(tmp_path, course):
    willing = learner("willing@example.org")
    declining = learner("declining@example.org", consent=False)
    question, right, _ = question_on(course["t1"])
    process_submission(user=willing, question_id=question.pk, choice_id=right.pk)
    process_submission(user=declining, question_id=question.pk, choice_id=right.pk)

    directory, output = export(tmp_path)
    pseudonyms = {row["pseudonym"] for row in read_csv(directory)}

    assert pseudonyms == {willing.research_pseudonym}
    assert declining.research_pseudonym not in every_file(directory)
    assert read_json(directory, "metadata.json")["counts"] == {
        "rows": 1,
        "learners": 1,
        "excluded_no_consent_rows": 1,
        "excluded_no_consent_learners": 1,
        "simulated_rows": 0,
        "simulated_learners": 0,
    }


def test_review_repeat_rows_are_not_exported(tmp_path, course):
    willing = learner("repeat@example.org")
    question, right, _ = question_on(course["t1"])
    process_submission(user=willing, question_id=question.pk, choice_id=right.pk)
    # The same question inside the review window is a review_repeat (D25): it
    # is logged, but a memorised answer is not new evidence.
    process_submission(user=willing, question_id=question.pk, choice_id=right.pk)

    assert AssessmentAttempt.objects.filter(source=AttemptSource.REVIEW_REPEAT).count() == 1

    directory, _ = export(tmp_path)
    rows = read_csv(directory)
    assert len(rows) == 1
    assert {row["source"] for row in rows} == {AttemptSource.ADAPTIVE}
    assert AttemptSource.REVIEW_REPEAT not in every_file(directory).split("sources_excluded")[0]


# ---------------------------------------------------------------------------
# Scope (D44)
# ---------------------------------------------------------------------------

def test_seed_simulated_and_legacy_rows_are_excluded(tmp_path, course):
    willing = learner("real@example.org")
    simulated = learner("sim@example.org", consent=True, simulated=True)
    question, right, _ = question_on(course["t1"])

    process_submission(user=willing, question_id=question.pk, choice_id=right.pk)
    process_submission(
        user=willing, question_id=question.pk, choice_id=right.pk,
        source=AttemptSource.SEED, answered_at=timezone.now(),
    )
    process_submission(
        user=simulated, question_id=question.pk, choice_id=right.pk,
        source=AttemptSource.SIMULATED, answered_at=timezone.now(),
    )
    # A legacy row predates the ledger, so it has no engine version; it is
    # written directly because record_attempt refuses to produce one.
    AssessmentAttempt.objects.create(
        user=willing, question=question, selected_choice=right, is_correct=True,
        topic=course["t1"], course=course["course"], attempt_no=99,
        source=AttemptSource.LEGACY,
    )

    directory, _ = export(tmp_path)
    rows = read_csv(directory)
    assert len(rows) == 1
    assert rows[0]["source"] == AttemptSource.ADAPTIVE
    assert rows[0]["engine_version"] == ENGINE_VERSION


def test_include_simulated_is_marked_as_not_a_thesis_result(tmp_path, course):
    simulated = learner("sim2@example.org", consent=False, simulated=True)
    seeded, right_seeded, _ = question_on(course["t1"], "q-sim")
    process_submission(
        user=simulated, question_id=seeded.pk, choice_id=right_seeded.pk,
        source=AttemptSource.SIMULATED, answered_at=timezone.now(),
    )
    # The simulator's own source is never exported; what the flag lets through
    # is an adaptive answer from a simulator account. It has to be another
    # question, or the second answer would be a review_repeat (D25).
    adaptive, right_adaptive, _ = question_on(course["t1"], "q-adaptive")
    process_submission(user=simulated, question_id=adaptive.pk, choice_id=right_adaptive.pk)

    with pytest.raises(CommandError, match="Nothing to export"):
        export(tmp_path, name="plain")

    directory, output = export(tmp_path, "--include-simulated", name="with-sim")
    metadata = read_json(directory, "metadata.json")
    assert metadata["thesis_result"] is False
    assert metadata["counts"]["simulated_rows"] == 1
    assert "not a thesis result" in output
    assert len(read_csv(directory)) == 1


def test_an_archived_topic_leaves_the_export(tmp_path, course):
    willing = learner("archived@example.org")
    first, right_first, _ = question_on(course["t1"], "q1")
    process_submission(user=willing, question_id=first.pk, choice_id=right_first.pk)

    other = make_topic("Boshqa", course["section"], slug="ex-t3", position=2)
    second, right_second, _ = question_on(other, "q2")
    process_submission(user=willing, question_id=second.pk, choice_id=right_second.pk)
    clear_local_cache()

    kb.archive_node(other)
    clear_local_cache()

    directory, _ = export(tmp_path)
    topics = {row["topic_id"] for row in read_csv(directory)}
    assert topics == {str(course["t1"].pk)}


def test_the_course_filter_restricts_the_export(tmp_path, course):
    willing = learner("twocourses@example.org")
    first, right_first, _ = question_on(course["t1"], "q1")
    process_submission(user=willing, question_id=first.pk, choice_id=right_first.pk)

    elsewhere = make_topic("Grafika", None, slug="ex-other-topic")
    second, right_second, _ = question_on(elsewhere, "q2")
    clear_local_cache()
    process_submission(user=willing, question_id=second.pk, choice_id=right_second.pk)

    directory, _ = export(tmp_path, "--course", str(course["course"].pk))
    assert {row["course_id"] for row in read_csv(directory)} == {str(course["course"].pk)}

    with pytest.raises(CommandError, match="does not exist or is archived"):
        export(tmp_path, "--course", "999999", name="missing")


# ---------------------------------------------------------------------------
# Control (D45)
# ---------------------------------------------------------------------------

def test_dry_run_reports_the_numbers_and_writes_nothing(tmp_path, course):
    willing = learner("dry@example.org")
    declining = learner("dry-no@example.org", consent=False)
    question, right, _ = question_on(course["t1"])
    process_submission(user=willing, question_id=question.pk, choice_id=right.pk)
    process_submission(user=declining, question_id=question.pk, choice_id=right.pk)

    out = tmp_path / "dry"
    buffer = StringIO()
    call_command("export_research_data", "--out", str(out), "--dry-run", stdout=buffer)
    output = buffer.getvalue()

    assert not out.exists()
    assert "nothing was written" in output
    # The two counts are reported apart, which is what D45 asks for.
    assert "Exported:  1 answer(s) from 1 learner(s)" in output
    assert "Excluded for no consent: 1 answer(s) from 1 learner(s)" in output


def test_an_empty_export_is_an_error_not_an_empty_directory(tmp_path, course):
    learner("nobody@example.org", consent=False)
    with pytest.raises(CommandError, match="Nothing to export"):
        export(tmp_path)


# ---------------------------------------------------------------------------
# The four files
# ---------------------------------------------------------------------------

def test_the_csv_carries_the_numbers_the_model_used(tmp_path, course):
    willing = learner("csv@example.org")
    question, right, _ = question_on(course["t1"], b=0.25)
    process_submission(user=willing, question_id=question.pk, choice_id=right.pk)

    directory, _ = export(tmp_path)
    row = read_csv(directory)[0]
    ledger = AssessmentAttempt.objects.get(user=willing)

    for column, value in (
        ("p_hat", ledger.p_hat),
        ("guess", ledger.guess_used),
        ("slip", ledger.slip_used),
        ("p_before", ledger.p_before),
        ("p_after", ledger.p_after),
        ("theta_before", ledger.theta_before),
        ("theta_after", ledger.theta_after),
        ("b_before", ledger.b_before),
        ("b_after", ledger.b_after),
        ("readiness_score", ledger.readiness_score),
    ):
        assert float(row[column]) == pytest.approx(value), column
    assert row["attempt_no"] == "1"
    assert row["was_ready"] == "True"
    assert row["kb_version"] == str(ledger.kb_version)


def test_the_pykt_file_is_one_block_per_learner(tmp_path, course):
    first = learner("seq1@example.org")
    second = learner("seq2@example.org")
    one, right_one, wrong_one = question_on(course["t1"], "q1")
    two, right_two, _ = question_on(course["t1"], "q2")

    process_submission(user=first, question_id=one.pk, choice_id=right_one.pk)
    process_submission(user=first, question_id=two.pk, choice_id=right_two.pk)
    process_submission(user=second, question_id=one.pk, choice_id=wrong_one.pk)

    directory, _ = export(tmp_path)
    lines = (directory / "pykt_sequences.txt").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 10  # two learners, five lines each

    blocks = {lines[index]: lines[index + 1:index + 5] for index in (0, 5)}
    header = f"{first.research_pseudonym},2"
    assert header in blocks
    questions, concepts, responses, timestamps = blocks[header]
    assert questions == f"{one.pk},{two.pk}"
    # The knowledge component of this model is the topic.
    assert concepts == f"{course['t1'].pk},{course['t1'].pk}"
    assert responses == "1,1"
    assert all(stamp.isdigit() for stamp in timestamps.split(","))

    assert blocks[f"{second.research_pseudonym},1"][2] == "0"


def test_the_graph_file_holds_the_tree_e_p_and_g_l(tmp_path, course):
    willing = learner("graph@example.org")
    question, right, _ = question_on(course["t1"])
    process_submission(user=willing, question_id=question.pk, choice_id=right.pk)

    directory, _ = export(tmp_path)
    graph = read_json(directory, "knowledge_base.json")
    snapshot = get_snapshot()

    assert graph["kb_version"] == snapshot.version
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert set(nodes) == set(snapshot.pos)
    assert nodes[course["course"].pk]["kind"] == "course"
    assert nodes[course["course"].pk]["parent"] is None
    assert nodes[course["t2"].pk]["lev"] == 1
    assert nodes[course["t1"].pk]["pos"] == snapshot.pos[course["t1"].pk]

    assert graph["prerequisites"] == [{
        "id": snapshot.prerequisites[0].id,
        "source": course["t1"].pk,
        "target": course["t2"].pk,
        "weight": 0.8,
    }]
    assert graph["leaf_edges"] == [{
        "source": course["t1"].pk,
        "target": course["t2"].pk,
        "weight": 0.8,
        "inherited": False,
        "via": [snapshot.prerequisites[0].id],
    }]


def test_the_metadata_says_which_data_the_results_came_from(tmp_path, course):
    willing = learner("meta@example.org")
    question, right, _ = question_on(course["t1"])
    process_submission(user=willing, question_id=question.pk, choice_id=right.pk)

    directory, _ = export(tmp_path)
    metadata = read_json(directory, "metadata.json")

    assert metadata["thesis_result"] is True
    assert metadata["kb_version"] == get_snapshot().version
    assert metadata["engine_versions"] == [ENGINE_VERSION]
    assert metadata["filters"]["engine_version_prefix"] == ENGINE_NAME
    assert metadata["filters"]["research_consent"] is True
    assert metadata["filters"]["is_simulated"] is False
    assert sorted(metadata["filters"]["sources"]) == ["adaptive", "test_session"]
    assert sorted(metadata["filters"]["sources_excluded"]) == [
        "legacy", "review_repeat", "seed", "simulated",
    ]
    assert metadata["identifiers"]["learner"] == "research_pseudonym"
    assert metadata["pykt_format"]["lines_per_learner"] == 5
    assert set(metadata["files"]) == {"pykt", "csv", "graph", "metadata"}
    assert set(metadata["files"].values()) == {path.name for path in directory.iterdir()}
    # The commit is read from git; absent outside a checkout, never invented.
    assert "code_commit" in metadata


def test_a_test_session_answer_is_exported_too(tmp_path, course):
    """``source ∈ {adaptive, test_session}`` (D44), not adaptive alone."""
    from assessments.services import test_session

    willing = learner("session@example.org")
    questions = [question_on(course["t1"], f"q{index}") for index in range(3)]
    paper = [
        {"question_id": question.pk, "choice_id": right.pk}
        for question, right, _ in questions
    ]
    test_session.submit(user=willing, topic_id=course["t1"].pk, answers=paper)

    directory, _ = export(tmp_path)
    assert {row["source"] for row in read_csv(directory)} == {AttemptSource.TEST_SESSION}

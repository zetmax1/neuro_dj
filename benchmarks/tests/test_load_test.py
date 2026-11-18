"""
benchmarks/tests/test_load_test.py — the stage 10 load test's own parts (SN3).

The Locust run itself is measured, not unit-tested; what is tested is what its
numbers rest on: the seed builds the course V-F2 describes (acyclic, the
sizes asked for, simulated learners only) and refuses any database with a
real account in it (D13), and the report reads p50, p95, the error share and
RPS from Locust's CSV into the right fields.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from assessments.models import Question
from benchmarks import load_test
from experiments import tables as result_tables
from curriculum.models import Topic, TopicKind, TopicPrerequisite
from curriculum.services.graph import build_snapshot

User = get_user_model()

SMALL = ("--topics", "30", "--prerequisites", "60", "--span", "6", "--questions", "3", "--learners", "4")


@pytest.mark.django_db
def test_the_seed_builds_the_course_it_is_asked_for(monkeypatch):
    monkeypatch.setenv("LOAD_TEST_PASSWORD", "load-test-only-password-0")
    call_command("seed_load_test", *SMALL, "--tag", "t1")

    topics = Topic.objects.filter(kind=TopicKind.TOPIC, slug__startswith="load-t")
    assert topics.count() == 30
    relations = TopicPrerequisite.objects.filter(topic__slug__startswith="load-t")
    assert relations.count() == 60
    assert all(
        int(x[len("load-t"):]) < int(y[len("load-t"):]) <= int(x[len("load-t"):]) + 6
        for x, y in relations.values_list("prerequisite__slug", "topic__slug")
    )
    snapshot = build_snapshot()  # raises if G_L had a cycle
    assert len(snapshot.order) == 30
    assert Question.objects.filter(topic__in=topics).count() == 30 * 3
    learners = User.objects.filter(email__startswith="load-t1-")
    assert learners.count() == 4
    assert all(u.is_simulated and u.check_password("load-test-only-password-0") for u in learners)


@pytest.mark.django_db
def test_the_seed_is_idempotent_and_gives_each_run_fresh_learners(monkeypatch):
    monkeypatch.setenv("LOAD_TEST_PASSWORD", "load-test-only-password-0")
    call_command("seed_load_test", *SMALL, "--tag", "a")
    call_command("seed_load_test", *SMALL[:-2], "--learners", "2", "--questions", "5", "--tag", "b")

    assert Topic.objects.filter(slug="load-course").count() == 1
    assert TopicPrerequisite.objects.filter(topic__slug__startswith="load-t").count() == 60
    assert Question.objects.filter(topic__slug__startswith="load-t").count() == 30 * 5  # topped up
    assert User.objects.filter(email__startswith="load-a-").count() == 4
    assert User.objects.filter(email__startswith="load-b-").count() == 2


@pytest.mark.django_db
def test_the_seed_refuses_a_database_with_a_real_account(monkeypatch):
    monkeypatch.setenv("LOAD_TEST_PASSWORD", "load-test-only-password-0")
    User.objects.create_user(email="real.person@example.org", password=None)

    with pytest.raises(CommandError, match="not simulated"):
        call_command("seed_load_test", *SMALL)
    assert not Topic.objects.filter(slug="load-course").exists()


@pytest.mark.django_db
def test_the_seed_needs_a_password_from_the_environment(monkeypatch):
    monkeypatch.delenv("LOAD_TEST_PASSWORD", raising=False)
    with pytest.raises(CommandError, match="LOAD_TEST_PASSWORD"):
        call_command("seed_load_test", *SMALL)


STATS_CSV = (
    "Type,Name,Request Count,Failure Count,Median Response Time,Average Response Time,"
    "Min Response Time,Max Response Time,Average Content Size,Requests/s,Failures/s,"
    "50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%\n"
    "POST,submit_answer,200,2,110,130.5,40,900,700,1.67,0.02,110,130,150,160,200,250,400,600,900,900,900\n"
    "GET,trajectory,0,0,0,0,0,0,0,0.0,0.0,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A,N/A\n"
    ",Aggregated,200,2,110,130.5,40,900,700,1.67,0.02,110,130,150,160,200,250,400,600,900,900,900\n"
)


def test_the_report_reads_locusts_percentiles_and_error_share(tmp_path):
    (tmp_path / "locust_stats.csv").write_text(STATS_CSV)

    stats = load_test.read_stats(tmp_path / "locust")

    assert stats["submit_answer"] == {
        "requests": 200, "failures": 2, "error_share": 0.01,
        "p50_ms": 110.0, "p95_ms": 250.0, "mean_ms": 130.5, "max_ms": 900.0, "rps": 1.67,
    }
    assert stats["trajectory"]["p95_ms"] is None and stats["trajectory"]["error_share"] == 0.0
    assert stats["Aggregated"]["requests"] == 200


def test_server_status_codes_are_counted_from_the_log(tmp_path):
    log = tmp_path / "server.log"
    log.write_text(
        '[20/Oct/2026 10:00:00] "GET /api/learning/trajectory/?course=1 HTTP/1.1" 200 5120\n'
        '[20/Oct/2026 10:00:01] "POST /api/assessments/submit_answer/ HTTP/1.1" 500 145\n'
        "Traceback (most recent call last):\n"
        '[20/Oct/2026 10:00:02] "GET /api/assessments/next_question/?topic_id=3 HTTP/1.1" 200 812\n'
    )
    assert load_test.server_statuses(log) == [
        {"status": 200, "count": 2}, {"status": 500, "count": 1},
    ]


def test_the_load_test_database_is_named_after_the_configured_one():
    url, name = load_test.locust_database_url("postgres://u:p@127.0.0.1:5433/neurolearn")
    assert name == "neurolearn_locust"
    assert url == "postgres://u:p@127.0.0.1:5433/neurolearn_locust"


def test_every_number_in_tables_md_is_a_value_in_metrics_json(tmp_path):
    """
    D48, checked by the project's own ``experiments.tables.verify`` (the same
    check ``tables.write`` applies before writing and the experiments suite
    applies to every published result). The first committed Locust runs broke
    it: the 300 ms target from a constant, status codes as dictionary keys,
    numbers formatted outside ``fmt``.
    """
    (tmp_path / "locust_stats.csv").write_text(STATS_CSV)
    endpoints = load_test.read_stats(tmp_path / "locust")
    for name in ("login", "next_question"):
        endpoints[name] = dict(endpoints["submit_answer"], rps=0.4166)
    endpoints["trajectory"] = dict(endpoints["submit_answer"], p95_ms=1600.0, rps=8.6125)
    metrics = {
        "run": {
            "users": 50, "duration_s": 120, "server": "django runserver", "debug": False,
            "cache": "Redis (redis://127.0.0.1:6380/3)", "db_conn_max_age": 0,
            "database": "neurolearn_locust", "course": {"topics": 500, "prerequisites": 1500},
        },
        "endpoints": endpoints,
        "v_f2_target_ms": load_test.V_F2_TARGET_MS,
        "locust_rounding_above_ms": load_test.LOCUST_ROUNDING_ABOVE_MS,
        "v_f2": {"submit_answer": "p95 250 ms — mo‘ljal ichida"},
        "server_statuses": [{"status": 200, "count": 3172}, {"status": 404, "count": 5}],
        "environment": {
            "cpu": {"model": "Test CPU", "logical_cores": 16, "governors": ["powersave"]},
            "memory_before": {"MemTotal": 15249, "MemAvailable": 6937, "SwapTotal": 4095, "SwapFree": 1864},
            "memory_during": {"samples": 25, "min_mem_available_mb": 6388, "min_swap_free_mb": 1864},
        },
        "provenance": {
            "tree_warnings": ["ishchi daraxt ishga tushirish boshida toza emas edi"],
            "code_commit": "5ab628e", "code_dirty": True, "command": "load_test.py",
        },
    }

    markdown = load_test.render(metrics)

    assert result_tables.verify(markdown, metrics) == []
    assert "| submit_answer | 200 | 2 | 0.01 | 110 | 250 | 1.67 |" in markdown
    assert markdown.startswith("> **Ogohlantirish (D54):**")


def test_the_quiet_machine_conditions_of_d68a():
    calm = {"MemTotal": 15249, "MemAvailable": 7000, "SwapTotal": 4095, "SwapFree": 4000}
    assert load_test.quiet_machine(calm, []) == []
    tight = dict(calm, MemAvailable=6000, SwapFree=3800)
    problems = load_test.quiet_machine(tight, [{"cpu_percent": 48.0, "command": "chrome"}])
    assert len(problems) == 3
    assert "6144 MB" in problems[0] and "295 MB" in problems[1] and "chrome 48.0%" in problems[2]


def test_gunicorn_runs_the_wsgi_app_with_the_access_log_the_report_reads():
    argv = load_test.server_command("gunicorn", 8, 8765)
    assert argv[1:4] == ["config.wsgi:application", "--workers", "8"]
    assert argv[argv.index("--access-logformat") + 1] == '"%(r)s" %(s)s %(B)s'
    assert load_test.server_command("runserver", None, 8765)[-2:] == ["127.0.0.1:8765", "--noreload"]

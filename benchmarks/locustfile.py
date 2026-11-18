"""
benchmarks/locustfile.py — the stage 10 load test (SN3, V-F2).

Each Locust user is one simulated learner of ``seed_load_test`` (D13). It
signs in the way the SPA does — the CSRF token first, then the token pair —
and then studies: ``next_question`` → ``submit_answer`` → ``trajectory``,
over and over, on the topic the trajectory puts first (Algorithm 2.5). Three
answers in four are correct, so topics are mastered and their successors open
during the run, which is the write path at its most expensive.

``next_question`` may answer 403 (the topic closed under the learner, TY1–TY4)
or 404 (no question left); both are answers the API is designed to give, so
they count as successes and the learner moves to another topic from the
trajectory. Every other non-2xx response is a failure.

Run it through ``benchmarks/load_test.py``, which seeds a dedicated database,
starts the server and writes the result with its provenance. Environment:
``LOAD_TEST_PASSWORD``, ``LOAD_TEST_COURSE``, ``LOAD_TEST_LEARNERS`` and
``LOAD_TEST_TAG`` (the run's learner accounts, ``seed_load_test --tag``).
"""

from __future__ import annotations

import itertools
import os
import random

from locust import HttpUser, between, task

PASSWORD = os.environ.get("LOAD_TEST_PASSWORD", "")
COURSE_ID = os.environ.get("LOAD_TEST_COURSE", "")
LEARNERS = int(os.environ.get("LOAD_TEST_LEARNERS", "50"))
TAG = os.environ.get("LOAD_TEST_TAG", "manual")
CORRECT_RATE = 0.75
# The seed marks the right option by its text; the learner "knows" it with
# probability CORRECT_RATE, which is all a simulated learner needs.
CORRECT_TEXT = "option 0"
EXPECTED_REFUSALS = (403, 404)
CLOSED_GROUP = "D"  # neuro_model.trajectory.GROUP_CLOSED; A review, B in progress, C open

_accounts = itertools.count()


class Learner(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self) -> None:
        index = next(_accounts) % LEARNERS
        self.rng = random.Random(index)
        self.topic: int | None = None
        self.skip: set[int] = set()  # topics that answered 403/404 to this learner

        csrf = self.client.get("/api/accounts/csrf/", name="csrf")
        # The CSRF cookie is Secure when DEBUG is off, so the HTTP client would
        # not send it back on its own; it is passed explicitly instead.
        login = self.client.post(
            "/api/accounts/token/",
            json={"email": f"load-{TAG}-{index:02d}@simulated.invalid", "password": PASSWORD},
            headers={"X-CSRFToken": csrf.json()["csrfToken"]},
            cookies={"csrftoken": csrf.cookies.get("csrftoken", "")},
            name="login",
        )
        self.client.headers["Authorization"] = f"Bearer {login.json()['access']}"
        self.trajectory()

    def trajectory(self) -> None:
        response = self.client.get(
            f"/api/learning/trajectory/?course={COURSE_ID}", name="trajectory",
        )
        body = response.json()
        head = body.get("next")
        if head and head["group"] != CLOSED_GROUP and head["topic_id"] not in self.skip:
            self.topic = head["topic_id"]
            return
        # The head is blocked or exhausted: any other topic that is not closed.
        candidates = [
            item["topic_id"] for item in body.get("items", ())
            if item["group"] != CLOSED_GROUP and item["topic_id"] not in self.skip
        ]
        self.topic = self.rng.choice(candidates) if candidates else None

    @task
    def study(self) -> None:
        if self.topic is None:
            self.trajectory()
            if self.topic is None:
                return

        with self.client.get(
            f"/api/assessments/next_question/?topic_id={self.topic}",
            name="next_question", catch_response=True,
        ) as response:
            if response.status_code in EXPECTED_REFUSALS:
                response.success()
                self.skip.add(self.topic)
                self.trajectory()
                return
            question = response.json()

        right = self.rng.random() < CORRECT_RATE
        choices = question["choices"]
        pick = next(
            (c for c in choices if (c["text"] == CORRECT_TEXT) == right),
            choices[0],
        )
        self.client.post(
            "/api/assessments/submit_answer/",
            json={"question_id": question["id"], "choice_id": pick["id"]},
            name="submit_answer",
        )
        self.trajectory()

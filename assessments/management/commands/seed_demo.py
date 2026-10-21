"""
seed_demo — synthetic demo data in Uzbek: two courses, two instructors and
thirty learners whose six weeks of answers went through the real answer path.

    manage.py seed_demo [--seed 20261021] [--password P] [--reset | --delete]

Synthetic data, not a research result: every account is ``is_simulated`` with
research consent off, and every answer is ``source=seed``, which the research
export never reads (D13, D44). See docs/DEMO_DATA.md.

Running it twice creates nothing twice. ``--reset`` removes the demo data and
builds it again; ``--delete`` only removes it. Both refuse, and change
nothing, when the demo courses hold anything that is not demo data
(``assessments.demo_seed.store``).

The password is never stored in the repository: it comes from ``--password``
or is generated and printed once, and only when this run creates accounts.
"""

from __future__ import annotations

import secrets
from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Max, Min

from assessments.models import AssessmentAttempt

from assessments.demo_seed import people, store

DEFAULT_SEED = 20261021
COURSE_LABELS = {people.PYTHON: "Python", people.ALGORITMLAR: "Algoritmlar"}


def _scale(value: str) -> float:
    scale = float(value)
    if not 0.0 < scale <= 1.0:
        raise ValueError("--scale must be in (0, 1]")
    return scale


class Command(BaseCommand):
    help = (
        "Seed synthetic demo data (Uzbek): two courses, two instructors, thirty "
        "learners with hidden profiles and six weeks of answers through the real "
        "answer path. Not research data. --reset rebuilds it, --delete removes it; "
        "nothing that is not demo data is ever touched."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Seed of names, profiles and answers.")
        parser.add_argument("--password", help="Password of every demo account (default: generated, printed once).")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--reset", action="store_true", help="Remove the demo data, then build it again.")
        group.add_argument("--delete", action="store_true", help="Remove the demo data and build nothing.")
        parser.add_argument(
            "--scale", type=_scale, default=1.0,
            help="Fraction of learners and sessions, for tests (default 1).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if options["reset"] or options["delete"]:
            before = store.present()
            try:
                removed = store.remove()
            except store.DemoDataError as exc:
                raise CommandError(
                    "Nothing was removed. The demo courses hold data that is not demo data:\n  - "
                    + "\n  - ".join(exc.problems)
                ) from exc
            self.stdout.write(
                f"Removed: {removed.users} demo account(s) with {before['answers']} answer(s), "
                f"{removed.nodes} demo node(s)."
            )
            if options["delete"]:
                return

        given = options.get("password")
        password = given or secrets.token_urlsafe(12)
        try:
            outcome = store.seed(seed=options["seed"], scale=options["scale"], password=password)
        except store.DemoDataError as exc:
            raise CommandError("; ".join(exc.problems)) from exc

        if outcome.simulated:
            self._summary(outcome)
        else:
            self.stdout.write(
                "Demo learners already exist: nothing was created twice. "
                "Use --reset to rebuild them."
            )
        if outcome.created_users:
            if given:
                self.stdout.write("Password of all demo accounts: the one given with --password.")
            else:
                self.stdout.write(f"Generated password of all demo accounts (shown once): {password}")
        elif given:
            count = store.set_password(given)
            self.stdout.write(f"Password set from --password on {count} demo account(s).")
        else:
            self.stdout.write("Passwords unchanged.")

        self._tables(seed=options["seed"], scale=options["scale"])
        self.stdout.write(self.style.WARNING(
            "Synthetic data — not a research result. Research consent is off for every demo "
            "account, and seed answers are never exported."
        ))

    # -- output -------------------------------------------------------------

    def _summary(self, outcome: store.SeedOutcome) -> None:
        rows = AssessmentAttempt.objects.filter(user__in=store.demo_users())
        span = rows.aggregate(first=Min("answered_at"), last=Max("answered_at"))
        by_profile = Counter()
        refused = Counter()
        exhausted = 0
        for learner in outcome.learners:
            by_profile[learner.person.profile] += learner.answers
            refused[learner.person.profile] += learner.refused
            exhausted += len(learner.exhausted)
        self.stdout.write(self.style.SUCCESS(
            f"Created {outcome.created_users} account(s); {rows.count()} answer(s) "
            f"from {span['first']:%Y-%m-%d %H:%M} to {span['last']:%Y-%m-%d %H:%M} UTC."
            if span["first"] else f"Created {outcome.created_users} account(s); no answers."
        ))
        self.stdout.write(
            "Answers by profile: "
            + ", ".join(f"{key} {by_profile[key]}" for key in (p.key for p in people.PROFILES))
        )
        self.stdout.write(
            f"Closed topics tried and refused by the readiness gate: {sum(refused.values())}; "
            f"(learner, topic) pairs with no question left: {exhausted}."
        )

    def _tables(self, *, seed: int, scale: float) -> None:
        rows = store.report(seed=seed, scale=scale)
        if not rows:
            return
        tau = settings.THESIS_MODEL["TAU"]
        labels = {profile.key: profile.label for profile in people.PROFILES}

        grouped: dict[str, list[store.StudentRow]] = defaultdict(list)
        for row in rows:
            grouped[row.profile].append(row)
        self.stdout.write("")
        self.stdout.write(
            f"By profile (P(L) ≥ τ = {tau}; ready = every prerequisite mastered, the topic not):"
        )
        header = ("Profile", "Learners", "Answers (mean)", "P(L)≥τ (mean)", "M=1 (mean)",
                  "Review (mean)", "Ready (mean)", "Next step (most common)")
        lines = [header]
        for key in [p.key for p in people.PROFILES] + [""]:
            group = grouped.get(key)
            if not group:
                continue
            nexts = Counter(name for row in group for _, name, _ in row.next_steps)
            lines.append((
                labels.get(key, "?"),
                str(len(group)),
                f"{mean(r.answers for r in group):.1f}",
                f"{mean(len(r.mastered) for r in group):.1f}",
                f"{mean(r.flagged for r in group):.1f}",
                f"{mean(r.review for r in group):.1f}",
                f"{mean(r.ready for r in group):.1f}",
                "; ".join(f"{name} ×{n}" for name, n in nexts.most_common(2)),
            ))
        self._print_table(lines)

        self.stdout.write("")
        self.stdout.write("By learner:")
        lines = [("Email", "Profile", "Courses", "Answers", "P(L)≥τ", "M=1", "Review", "Ready", "Next step")]
        for row in sorted(rows, key=lambda r: ([p.key for p in people.PROFILES] + [""]).index(r.profile)):
            lines.append((
                row.email,
                labels.get(row.profile, "?"),
                "+".join(COURSE_LABELS[key] for key in row.courses),
                str(row.answers),
                str(len(row.mastered)),
                str(row.flagged),
                str(row.review),
                str(row.ready),
                " | ".join(f"{COURSE_LABELS[key]}: {name}" for key, name, _ in row.next_steps),
            ))
        self._print_table(lines)
        distinct = len({row.pair for row in rows})
        self.stdout.write(
            f"Distinct (mastered set, next step) pairs: {distinct} of {len(rows)} learners."
        )

    def _print_table(self, lines: list[tuple[str, ...]]) -> None:
        widths = [max(len(line[i]) for line in lines) for i in range(len(lines[0]))]
        for number, line in enumerate(lines):
            self.stdout.write("  ".join(cell.ljust(width) for cell, width in zip(line, widths)).rstrip())
            if number == 0:
                self.stdout.write("  ".join("-" * width for width in widths))

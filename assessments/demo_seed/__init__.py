"""
assessments/demo_seed — the synthetic demo data of ``manage.py seed_demo``.

Two courses in Uzbek (Latin), two instructors and thirty learners with hidden
profiles whose answers are simulated and pushed through the real answer path
(``process_submission``), so P(L), θ, b_q, readiness and the trajectory are
whatever the system computes. Nothing here is research data: every account is
``is_simulated``, has no research consent, and every answer is ``source=seed``,
which the research export never reads (D13, D44).

- ``content``   — the two courses: sections, topics, questions, prerequisites;
- ``people``    — names, profiles and the roster drawn from the seed;
- ``simulator`` — the hidden learner and the event loop over six weeks;
- ``store``     — the demo markers, building, resetting and reporting.
"""

"""
experiments/ — the thesis experiments (stage 8b).

Two rules hold everywhere in this package.

**D48 — a result exists only if it was produced.** ``tables.md`` is generated
from ``metrics.json`` and from nothing else; every number it prints is a scalar
that is already in the metrics file. A dataset that is not on this machine
produces a row that says so, never a number borrowed from a paper. Every result
carries the sha256 of the files it was computed from, the code commit, the seed
and the command line.

**D49 — nothing is downloaded.** Every loader takes a path. The datasets are
fetched by hand (see ``experiments/data/README.md``) because two of them are
licensed and one is behind an access request, and because a script that
silently re-downloads a dataset cannot promise that two runs saw the same
bytes. The sha256 in the results is what makes that promise instead.

The computations of chapter II are not reimplemented here: ``graph_report``
calls ``neuro_model.graph`` and ``neuro_model.readiness``. Where a statistic
has no definition in chapter II — weakly connected components, strongly
connected components — it lives in this package and is checked against
networkx, which is a test dependency and never used by the code under test.
"""

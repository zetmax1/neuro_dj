# experiments/tests/fixtures

**Everything in this directory is synthetic.** None of it is published data,
and no number computed from it belongs in the thesis (D48).

The fixtures exist because the real datasets are not in the repository (D49)
and two of the paths that have to be tested are not exercised by any of them:

| File | Why it exists |
|---|---|
| `tiny.graphml` | A name key that is not `d0`, a self-loop (Y2), a duplicate edge and an isolated node — all in five nodes. |
| `tiny_edges.csv` | The `src,dst` CSV form of the same graph, without the loop. |
| `cyclic.graphml` | A strongly connected component. All four published graphs are acyclic, so the Y3 branch of `graph_report` has nothing real to run on. |
| `as09_tiny.csv` | The ASSISTments 2009 column layout with a blank `skill_id`, a duplicate `(order_id, skill_id)`, a question tagged with two skills and both values of `original` — the four cases D50's rules decide. |

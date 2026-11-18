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
| `junyi_exercise_table_tiny.csv` | The Junyi exercise-table layout with every case D61's rules decide: a repeated exercise name, a prerequisite cell listing the same name twice, a self-loop (Y2), a two-node cycle (Y3, merged by Tarjan), a prerequisite that is not an exercise, and a `live=FALSE` row. |
| `junyi_problem_log_tiny.csv` | The Junyi problem-log layout with a row for an exercise the table does not have, a row with no `time_done`, a `review_mode` answer (kept) and a `topic_mode` one. |
| `junyi_exercise_table_small.csv` | A six-exercise graph (two roots, two middles, two tops) that the synthetic log of `conftest.junyi_small` is generated against, so H1 and H3 have five folds to run on. |

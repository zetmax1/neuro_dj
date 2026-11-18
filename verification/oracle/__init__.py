"""
verification.oracle — an independent implementation of chapter II, sections 3.1
and 3.2, written from NEUROLEARN_REMEDIATION.md.

Rule 2: no line here is copied from ``neuro_model`` or ``curriculum``. Where the
specification names a standard graph property (acyclicity, longest path,
descendants, transitive reduction, lexicographically smallest topological
order), the oracle delegates to ``networkx`` rather than reimplementing it.
"""

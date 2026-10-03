"""
The reference course of NEUROLEARN_REMEDIATION.md section 4 as plain data.

Course "Ma'lumotlar tuzilmalari" with three sections; sections and the topics
inside them appear in this order (``position`` 0, 1, 2 ...).

E_P: t1->t3, t1->t5, t2->t4, t3->t6, t5->t6, t6->t7, t6->t8, t4->B3
("x->y" = x must be mastered before y).
"""

from __future__ import annotations

COURSE = ("course", "Ma'lumotlar tuzilmalari", None)

# slug -> (kind, name, parent slug)
NODES: dict[str, tuple[str, str, str | None]] = {
    "course": COURSE,
    "B1": ("section", "B1", "course"),
    "t1": ("topic", "Massivlar", "B1"),
    "t2": ("topic", "Funksiyalar", "B1"),
    "t3": ("topic", "Ko'rsatkichlar", "B1"),
    "B2": ("section", "B2", "course"),
    "t4": ("topic", "Rekursiya", "B2"),
    "t5": ("topic", "Ikkilik qidiruv", "B2"),
    "B3": ("section", "B3", "course"),
    "t6": ("topic", "Ikkilik qidiruv daraxti", "B3"),
    "t7": ("topic", "AVL daraxti", "B3"),
    "t8": ("topic", "Daraxtni aylanib chiqish", "B3"),
}

# Creation order fixes ``position`` inside every parent (0, 1, 2 ...).
ORDER: tuple[str, ...] = (
    "course", "B1", "t1", "t2", "t3", "B2", "t4", "t5", "B3", "t6", "t7", "t8",
)

# (prerequisite slug, topic slug)
PREREQUISITES: tuple[tuple[str, str], ...] = (
    ("t1", "t3"),
    ("t1", "t5"),
    ("t2", "t4"),
    ("t3", "t6"),
    ("t5", "t6"),
    ("t6", "t7"),
    ("t6", "t8"),
    ("t4", "B3"),
)

# Section-4 expectations, written out so the tests read like the table.
EXPECTED_EL: frozenset[tuple[str, str]] = frozenset({
    ("t1", "t3"), ("t1", "t5"), ("t2", "t4"), ("t3", "t6"), ("t5", "t6"),
    ("t6", "t7"), ("t6", "t8"), ("t4", "t6"), ("t4", "t7"), ("t4", "t8"),
})
EXPECTED_ORDER: tuple[str, ...] = ("t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8")
EXPECTED_LEV: dict[str, int] = {
    "t1": 0, "t2": 0, "t3": 1, "t4": 1, "t5": 1, "t6": 2, "t7": 3, "t8": 3,
}
EXPECTED_FIFO_ORDER: tuple[str, ...] = ("t1", "t2", "t3", "t5", "t4", "t6", "t7", "t8")
EXPECTED_DESC_SIZES: dict[str, int] = {
    "t1": 5, "t2": 4, "t3": 3, "t4": 3, "t5": 3, "t6": 2, "t7": 0, "t8": 0,
}
EXPECTED_REDUNDANT: frozenset[tuple[str, str]] = frozenset({("t4", "t7"), ("t4", "t8")})
EXPECTED_KAPPA: int = 0

# The rejections of section 4 / V-B2: (prerequisite, topic) -> reason.
EXPECTED_REJECTIONS: tuple[tuple[str, str, str], ...] = (
    ("t8", "t3", "cycle"),
    ("B3", "t6", "nested"),
)
EXPECTED_CYCLE_CHAIN: tuple[str, ...] = ("t3", "t6", "t8")

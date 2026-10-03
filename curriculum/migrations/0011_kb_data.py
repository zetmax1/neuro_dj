"""
Stage 2 data step (BB1, Y2–Y4).

Kinds: a root is a ``course``; a node with children is a ``section``; a leaf
is a ``topic`` (also when it has no questions yet — decision Q2-2; the spec's
"leaf without questions → section" rule was overridden by the user).

The migration stops instead of guessing when
- a course or section holds questions (Y4), or
- an existing prerequisite relation violates Y2 or makes G_L cyclic (Y3).
Nothing is deleted or moved here; see REMEDIATION_PROGRESS.md, Q2-1.

The checks are written out in this file on purpose: migrations must not
depend on application code that may change later.
"""

from collections import defaultdict, deque

from django.db import migrations


class KBMigrationStopped(RuntimeError):
    pass


def _ancestors(parent, node):
    out, current = [], parent.get(node)
    while current is not None:
        out.append(current)
        current = parent.get(current)
    return out


def classify_and_validate(apps, schema_editor):
    Topic = apps.get_model("curriculum", "Topic")
    Prerequisite = apps.get_model("curriculum", "TopicPrerequisite")
    Question = apps.get_model("assessments", "Question")
    Version = apps.get_model("curriculum", "KnowledgeBaseVersion")

    rows = list(Topic.objects.values_list("id", "parent_id", "name", "is_archived"))
    parent = {pk: parent_id for pk, parent_id, _, _ in rows}
    name = {pk: n for pk, _, n, _ in rows}
    has_children = {parent_id for _, parent_id, _, _ in rows if parent_id is not None}

    kind = {}
    for pk, parent_id, _, _ in rows:
        if parent_id is None:
            kind[pk] = "course"
        elif pk in has_children:
            kind[pk] = "section"
        else:
            kind[pk] = "topic"

    with_questions = set(Question.objects.values_list("topic_id", flat=True).distinct())
    mixed = sorted(pk for pk in with_questions if kind.get(pk) != "topic")
    if mixed:
        listing = ", ".join(f"[{pk}] {name[pk]} ({kind[pk]})" for pk in mixed)
        raise KBMigrationStopped(
            "Y4: questions may only belong to topics (leaves), but these nodes "
            f"are courses or sections with questions: {listing}. Move or delete "
            "those questions, then run the migration again."
        )

    by_kind = defaultdict(list)
    for pk, k in kind.items():
        by_kind[k].append(pk)
    for k, ids in by_kind.items():
        Topic.objects.filter(pk__in=ids).update(kind=k)

    # Y2 and Y3 on the active knowledge base.
    active = {pk for pk, _, _, archived in rows if not archived}
    children = defaultdict(list)
    for pk in active:
        if parent[pk] in active:
            children[parent[pk]].append(pk)

    def leaves(node):
        out, stack = set(), [node]
        while stack:
            n = stack.pop()
            if kind[n] == "topic":
                out.add(n)
            stack.extend(children[n])
        return out

    relations = [
        (x, y) for x, y in Prerequisite.objects.values_list("prerequisite_id", "topic_id")
        if x in active and y in active
    ]
    nested = [
        (x, y) for x, y in relations
        if x == y or x in _ancestors(parent, y) or y in _ancestors(parent, x)
    ]
    if nested:
        raise KBMigrationStopped(
            "Y2: prerequisite relations between a node and its ancestor: "
            + ", ".join(f"{name[x]} -> {name[y]}" for x, y in nested)
        )

    edges = {(a, b) for x, y in relations for a in leaves(x) for b in leaves(y) if a != b}
    topics = {pk for pk in active if kind[pk] == "topic"}
    indeg = {t: 0 for t in topics}
    succ = defaultdict(list)
    for a, b in edges:
        succ[a].append(b)
        indeg[b] += 1
    queue = deque(t for t in topics if indeg[t] == 0)
    seen = 0
    while queue:
        v = queue.popleft()
        seen += 1
        for w in succ[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                queue.append(w)
    if seen != len(topics):
        stuck = sorted(t for t in topics if indeg[t] > 0)
        raise KBMigrationStopped(
            "Y3: the inherited prerequisite graph has a cycle among: "
            + ", ".join(name[t] for t in stuck)
        )

    Version.objects.update_or_create(id=1, defaults={"version": 1})


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0010_kb_schema'),
        ('assessments', '0005_add_irt_fields_and_userability'),
    ]

    operations = [
        migrations.RunPython(classify_and_validate, migrations.RunPython.noop),
    ]

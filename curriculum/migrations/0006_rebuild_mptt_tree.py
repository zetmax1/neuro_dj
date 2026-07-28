"""
Data migration: Populate lft/rght/tree_id/level for all existing Topic rows.

This migration runs AFTER 0005_migrate_to_mptt (which adds the MPTT columns)
and uses Topic.objects.rebuild() to compute correct nested-set values from
the existing parent_id relationships.

This is a one-time migration — once run, MPTT auto-manages these fields on
all subsequent INSERT/UPDATE/DELETE operations.
"""

from django.db import migrations


def rebuild_mptt_tree(apps, schema_editor):
    """
    Populate MPTT columns (lft, rght, tree_id, level) for all existing
    Topic rows using the real MPTTModel.rebuild() method.

    We import the actual Topic model (not the historical one from apps)
    because apps.get_model() returns a plain model without MPTT's
    custom manager and rebuild() capability.
    """
    from curriculum.models import Topic
    Topic.objects.rebuild()


def noop_reverse(apps, schema_editor):
    """
    Reverse is a no-op — the MPTT columns will remain with their values.
    The previous migration will drop the columns if reversed.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0005_migrate_to_mptt'),
    ]

    operations = [
        migrations.RunPython(
            rebuild_mptt_tree,
            reverse_code=noop_reverse,
        ),
    ]

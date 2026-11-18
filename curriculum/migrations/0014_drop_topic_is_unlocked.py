"""
Stage 4: the global unlock flag is gone.

``Topic.is_unlocked`` was one flag for every learner, set by a parent-to-child
cascade. Readiness is per learner and comes from the M flags of Pre(w) in G_L
(3.4), so the column has no meaning any more and nothing reads it.
"""


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0013_kb_version_instance_token'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='topic',
            name='is_unlocked',
        ),
    ]

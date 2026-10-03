"""
Stage 4: ``StudentTopicState`` replaces ``UserKnowledgeState``.

The old row mixed two scales in one column: ``mastery_percentage`` held a
probability for rows the engine wrote and a 0-100 test grade for others. Those
values are **not** migrated — there is no safe reading of them. The table is
dropped and the states are rebuilt from the answer ledger with
``rebuild_student_states``, which replays Algorithm 2.4 and Algorithm 2.3 in
order (D35).

The new row carries P(L), the M flag with its τ/δ hysteresis, the status, the
``missing_count`` of Algorithm 2.3 and the ``kb_version`` of TY6.
"""


import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0009_student_model'),
        ('curriculum', '0014_drop_topic_is_unlocked'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentTopicState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('p_mastery', models.FloatField(default=0.0, help_text='P(L) — the mastery probability, never a percentage.')),
                ('mastered_flag', models.BooleanField(db_index=True, default=False, help_text='M, with τ/δ hysteresis; stored because it is not a function of p_mastery alone.')),
                ('status', models.CharField(choices=[('closed', 'Closed'), ('open', 'Open'), ('in_progress', 'In progress'), ('mastered', 'Mastered'), ('review', 'Review')], db_index=True, default='closed', max_length=12)),
                ('missing_count', models.PositiveIntegerField(default=0, help_text='Immediate predecessors in G_L with M = 0.')),
                ('started_at', models.DateTimeField(blank=True, help_text='When the learner first answered this topic; never cleared (TY5).', null=True)),
                ('kb_version', models.PositiveBigIntegerField(default=0, help_text='KB version the counter was computed under (TY6).')),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('correct', models.PositiveIntegerField(default=0)),
                ('accuracy', models.FloatField(default=0.0, help_text='correct / attempts, in [0, 1]; 0 before the first answer.')),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Student Topic State',
                'verbose_name_plural': 'Student Topic States',
            },
        ),
        migrations.RemoveIndex(
            model_name='userknowledgestate',
            name='idx_user_mastery',
        ),
        migrations.RemoveConstraint(
            model_name='userknowledgestate',
            name='uniq_user_topic_state',
        ),
        migrations.AddField(
            model_name='studenttopicstate',
            name='topic',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_states', to='curriculum.topic'),
        ),
        migrations.AddField(
            model_name='studenttopicstate',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='topic_states', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RemoveField(
            model_name='userknowledgestate',
            name='topic',
        ),
        migrations.RemoveField(
            model_name='userknowledgestate',
            name='user',
        ),
        migrations.AddIndex(
            model_name='studenttopicstate',
            index=models.Index(fields=['user', 'status'], name='idx_state_user_status'),
        ),
        migrations.AddConstraint(
            model_name='studenttopicstate',
            constraint=models.UniqueConstraint(fields=('user', 'topic'), name='uniq_student_topic_state'),
        ),
        migrations.AddConstraint(
            model_name='studenttopicstate',
            constraint=models.CheckConstraint(condition=models.Q(('p_mastery__gte', 0.0), ('p_mastery__lte', 1.0)), name='state_p_mastery_is_a_probability'),
        ),
        migrations.AddConstraint(
            model_name='studenttopicstate',
            constraint=models.CheckConstraint(condition=models.Q(('accuracy__gte', 0.0), ('accuracy__lte', 1.0)), name='state_accuracy_is_a_fraction'),
        ),
        migrations.AddConstraint(
            model_name='studenttopicstate',
            constraint=models.CheckConstraint(condition=models.Q(('correct__lte', models.F('attempts'))), name='state_correct_within_attempts'),
        ),
        migrations.AddConstraint(
            model_name='studenttopicstate',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('status__in', ['in_progress', 'mastered', 'review']), ('started_at__isnull', False)), models.Q(('status__in', ['closed', 'open']), ('started_at__isnull', True)), _connector='OR'), name='state_started_matches_status'),
        ),
        migrations.DeleteModel(
            name='UserKnowledgeState',
        ),
    ]

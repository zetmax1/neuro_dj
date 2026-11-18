"""
Stage 3 (D33): the student model moves to the chapter II parameters.

``UserAbility`` becomes a per-course row with its own answer counter. The
existing per-topic rows are **not** migrated: they hold θ values produced by
the removed engines at topic level, which has no meaning in the new semantics.
They are deleted and the count is printed, so every learner starts from
θ = 0, n_answers = 0.

``Question.n_answers`` starts at 0 for the same reason: back-filling it from
legacy answers would shrink the Elo step size for evidence the new model never
saw, and would move b_q on the strength of the old engines' question choices.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def drop_topic_level_abilities(apps, schema_editor):
    Ability = apps.get_model("assessments", "UserAbility")
    removed = Ability.objects.count()
    Ability.objects.all().delete()
    print(
        f"\n  D33: removed {removed} per-topic UserAbility row(s); "
        "ability is now estimated per course from θ = 0."
    )


def noop(apps, schema_editor):
    """The old θ values are gone for good; reversing restores an empty table."""


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0008_enforce_attempt_ledger'),
        ('curriculum', '0013_kb_version_instance_token'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # The table is emptied first, so the non-null course column below needs
        # no default and no back-fill.
        migrations.RunPython(drop_topic_level_abilities, noop),
        migrations.RemoveConstraint(
            model_name='userability',
            name='uniq_user_topic_ability',
        ),
        migrations.RemoveField(
            model_name='userability',
            name='topic',
        ),
        migrations.AddField(
            model_name='userability',
            name='course',
            field=models.ForeignKey(
                default=None,
                help_text='Root of the tree (kind=course, D2).',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='abilities',
                to='curriculum.topic',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userability',
            name='n_answers',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Answers this learner has given in this course.',
            ),
        ),
        migrations.AlterField(
            model_name='userability',
            name='theta',
            field=models.FloatField(
                default=0.0,
                help_text="Ability θ_s, clamped to ±THESIS_MODEL['THETA_CLAMP'].",
            ),
        ),
        migrations.AddConstraint(
            model_name='userability',
            constraint=models.UniqueConstraint(
                fields=('user', 'course'), name='uniq_user_course_ability',
            ),
        ),
        migrations.AddField(
            model_name='question',
            name='n_answers',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Answers recorded for this question; the Elo step size shrinks as it grows.',
            ),
        ),
        migrations.AlterField(
            model_name='question',
            name='irt_difficulty',
            field=models.FloatField(
                default=0.0,
                help_text='Item difficulty b_q, moved by Elo after every answer (3.3).',
            ),
        ),
        migrations.AlterField(
            model_name='userknowledgehistory',
            name='algorithm_used',
            field=models.CharField(
                choices=[
                    ('thesis_hybrid', 'Thesis hybrid (BKT + IRT + prerequisites)'),
                    ('streak', 'Streak Estimation (removed)'),
                    ('bkt', 'Bayesian Knowledge Tracing (removed)'),
                    ('irt', 'Item Response Theory (removed)'),
                    ('hybrid_bkt_irt', 'Hybrid BKT + IRT (removed)'),
                ],
                help_text='Which estimation engine produced this data point.',
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name='TopicModelParams',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('p0', models.FloatField(help_text='P0 — the base prior of this topic.')),
                ('pt', models.FloatField(help_text='PT — the learning rate per opportunity.')),
                ('g0', models.FloatField(help_text='G0 — the base guess rate; must be < G_MAX.')),
                ('s0', models.FloatField(help_text='S0 — the base slip rate; must be < S_MAX.')),
                ('source', models.CharField(
                    choices=[('default', 'Default'), ('fitted', 'Fitted')],
                    db_index=True, default='default', max_length=10,
                )),
                ('fitted_at', models.DateTimeField(
                    blank=True, null=True,
                    help_text='When calibration produced these values; NULL for defaults.',
                )),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('topic', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='model_params',
                    to='curriculum.topic',
                )),
            ],
            options={
                'verbose_name': 'Topic Model Parameters',
                'verbose_name_plural': 'Topic Model Parameters',
            },
        ),
        migrations.AddConstraint(
            model_name='topicmodelparams',
            constraint=models.CheckConstraint(
                condition=models.Q(('p0__gt', 0.0), ('p0__lt', 1.0)), name='params_p0_range',
            ),
        ),
        migrations.AddConstraint(
            model_name='topicmodelparams',
            constraint=models.CheckConstraint(
                condition=models.Q(('pt__gte', 0.0), ('pt__lte', 1.0)), name='params_pt_range',
            ),
        ),
        migrations.AddConstraint(
            model_name='topicmodelparams',
            constraint=models.CheckConstraint(
                condition=models.Q(('g0__gt', 0.0), ('g0__lt', 1.0)), name='params_g0_range',
            ),
        ),
        migrations.AddConstraint(
            model_name='topicmodelparams',
            constraint=models.CheckConstraint(
                condition=models.Q(('s0__gt', 0.0), ('s0__lt', 1.0)), name='params_s0_range',
            ),
        ),
        migrations.AddConstraint(
            model_name='topicmodelparams',
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(('fitted_at__isnull', True), ('source', 'default')),
                    models.Q(('fitted_at__isnull', False), ('source', 'fitted')),
                    _connector='OR',
                ),
                name='params_fitted_at_matches_source',
            ),
        ),
    ]

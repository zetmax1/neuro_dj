"""
Stage 1 (D10, D11, TM7): answer-ledger columns, test-session results and the
history -> attempt link. Ledger identity columns are added nullable here, filled
for existing rows in 0007 and made mandatory in 0008, so each step commits
separately (PostgreSQL refuses ALTER TABLE with pending FK trigger events).
"""

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0005_add_irt_fields_and_userability'),
        ('curriculum', '0009_topic_is_archived'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TestSessionResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_questions', models.PositiveIntegerField()),
                ('earned_points', models.PositiveIntegerField()),
                ('total_points', models.PositiveIntegerField()),
                ('score_percentage', models.FloatField(help_text='Difficulty-weighted grade, 0–100.')),
                ('pass_mark_percentage', models.FloatField(help_text='Pass mark of the topic when the test was taken.')),
                ('passed', models.BooleanField()),
                ('submitted_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('topic', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='test_sessions', to='curriculum.topic')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-submitted_at'],
                'indexes': [models.Index(fields=['user', 'topic', 'submitted_at'], name='idx_session_user_topic_ts')],
                'constraints': [models.CheckConstraint(condition=models.Q(('score_percentage__gte', 0), ('score_percentage__lte', 100)), name='session_score_in_range')],
            },
        ),
        # D11: answers keep their question, choice and topic.
        migrations.AlterField(
            model_name='assessmentattempt',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='attempts', to='assessments.question'),
        ),
        migrations.AlterField(
            model_name='assessmentattempt',
            name='selected_choice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='selections', to='assessments.choice'),
        ),
        # Seeds back-date answers at insert time instead of rewriting rows later.
        migrations.AlterField(
            model_name='assessmentattempt',
            name='answered_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='topic',
            field=models.ForeignKey(null=True, help_text='Topic of the question at answer time.', on_delete=django.db.models.deletion.PROTECT, related_name='attempts', to='curriculum.topic'),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='course',
            field=models.ForeignKey(null=True, help_text="Root of the topic's tree at answer time.", on_delete=django.db.models.deletion.PROTECT, related_name='course_attempts', to='curriculum.topic'),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='attempt_no',
            field=models.PositiveIntegerField(null=True, help_text='1, 2, 3, … per (user, topic), in recording order.'),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='source',
            field=models.CharField(choices=[('adaptive', 'Adaptive practice'), ('test_session', 'Test session'), ('review_repeat', 'Same question repeated within the review window'), ('seed', 'Demo seed'), ('simulated', 'Simulated learner'), ('legacy', 'Recorded before the ledger existed')], db_index=True, default='legacy', max_length=20),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='session',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='attempts', to='assessments.testsessionresult'),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='p_before',
            field=models.FloatField(blank=True, help_text='P(L) before the update.', null=True),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='p_hat',
            field=models.FloatField(blank=True, help_text='Predicted P(correct).', null=True),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='p_after',
            field=models.FloatField(blank=True, help_text='P(L) after the update.', null=True),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='guess_used',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='slip_used',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='theta_before',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='theta_after',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='b_before',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='b_after',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='readiness_score',
            field=models.FloatField(blank=True, help_text='r_s(w) at answer time.', null=True),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='was_ready',
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='engine_version',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='assessmentattempt',
            name='kb_version',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userknowledgehistory',
            name='attempt',
            field=models.OneToOneField(blank=True, help_text='Answer that produced this value (NULL for rows written before the ledger).', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='history_entry', to='assessments.assessmentattempt'),
        ),
        migrations.AlterField(
            model_name='userknowledgehistory',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]

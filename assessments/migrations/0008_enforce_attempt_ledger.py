"""Stage 1 (D10): ledger identity columns become mandatory and constrained."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0007_backfill_legacy_attempts'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessmentattempt',
            name='topic',
            field=models.ForeignKey(help_text='Topic of the question at answer time.', on_delete=django.db.models.deletion.PROTECT, related_name='attempts', to='curriculum.topic'),
        ),
        migrations.AlterField(
            model_name='assessmentattempt',
            name='course',
            field=models.ForeignKey(help_text="Root of the topic's tree at answer time.", on_delete=django.db.models.deletion.PROTECT, related_name='course_attempts', to='curriculum.topic'),
        ),
        migrations.AlterField(
            model_name='assessmentattempt',
            name='attempt_no',
            field=models.PositiveIntegerField(help_text='1, 2, 3, … per (user, topic), in recording order.'),
        ),
        # No default: every writer must state where an answer came from.
        migrations.AlterField(
            model_name='assessmentattempt',
            name='source',
            field=models.CharField(choices=[('adaptive', 'Adaptive practice'), ('test_session', 'Test session'), ('review_repeat', 'Same question repeated within the review window'), ('seed', 'Demo seed'), ('simulated', 'Simulated learner'), ('legacy', 'Recorded before the ledger existed')], db_index=True, max_length=20),
        ),
        migrations.AddConstraint(
            model_name='assessmentattempt',
            constraint=models.UniqueConstraint(fields=('user', 'topic', 'attempt_no'), name='uniq_attempt_user_topic_no'),
        ),
        migrations.AddConstraint(
            model_name='assessmentattempt',
            constraint=models.CheckConstraint(condition=models.Q(('attempt_no__gte', 1)), name='attempt_no_starts_at_one'),
        ),
        migrations.AddConstraint(
            model_name='assessmentattempt',
            constraint=models.CheckConstraint(condition=models.Q(('source__in', ['adaptive', 'test_session', 'review_repeat', 'seed', 'simulated', 'legacy'])), name='attempt_source_valid'),
        ),
        migrations.AddConstraint(
            model_name='assessmentattempt',
            constraint=models.CheckConstraint(condition=models.Q(('p_before__isnull', True), models.Q(('p_before__gte', 0), ('p_before__lte', 1)), _connector='OR'), name='attempt_p_before_is_probability'),
        ),
        migrations.AddConstraint(
            model_name='assessmentattempt',
            constraint=models.CheckConstraint(condition=models.Q(('p_hat__isnull', True), models.Q(('p_hat__gte', 0), ('p_hat__lte', 1)), _connector='OR'), name='attempt_p_hat_is_probability'),
        ),
        migrations.AddConstraint(
            model_name='assessmentattempt',
            constraint=models.CheckConstraint(condition=models.Q(('p_after__isnull', True), models.Q(('p_after__gte', 0), ('p_after__lte', 1)), _connector='OR'), name='attempt_p_after_is_probability'),
        ),
        migrations.AddConstraint(
            model_name='assessmentattempt',
            constraint=models.CheckConstraint(condition=models.Q(('guess_used__isnull', True), models.Q(('guess_used__gte', 0), ('guess_used__lte', 1)), _connector='OR'), name='attempt_guess_used_is_probability'),
        ),
        migrations.AddConstraint(
            model_name='assessmentattempt',
            constraint=models.CheckConstraint(condition=models.Q(('slip_used__isnull', True), models.Q(('slip_used__gte', 0), ('slip_used__lte', 1)), _connector='OR'), name='attempt_slip_used_is_probability'),
        ),
        migrations.AddConstraint(
            model_name='assessmentattempt',
            constraint=models.CheckConstraint(condition=models.Q(('readiness_score__isnull', True), models.Q(('readiness_score__gte', 0), ('readiness_score__lte', 1)), _connector='OR'), name='attempt_readiness_score_is_probability'),
        ),
    ]

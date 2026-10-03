"""
Stage 2 (BB1, BB3, D4): add ``kind`` (nullable until 0011 fills it), the
prerequisite weight ω and the KB version singleton. MPTT columns are dropped
in 0012, after the data step has committed.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0009_topic_is_archived'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='kind',
            field=models.CharField(choices=[('course', 'Course'), ('section', 'Section'), ('topic', 'Topic')], db_index=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='topicprerequisite',
            name='weight',
            field=models.FloatField(default=1.0, help_text='ω ∈ (0, 1]; default 1.'),
        ),
        migrations.CreateModel(
            name='KnowledgeBaseVersion',
            fields=[
                ('id', models.PositiveSmallIntegerField(default=1, primary_key=True, serialize=False)),
                ('version', models.PositiveBigIntegerField(default=1)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'constraints': [models.CheckConstraint(condition=models.Q(('id', 1)), name='kb_version_singleton')],
            },
        ),
    ]

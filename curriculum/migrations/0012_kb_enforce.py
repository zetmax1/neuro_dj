"""
Stage 2 (D3, BB1, BB3): the tree moves from django-mptt to an adjacency list
read with recursive CTEs (django-tree-queries); ``kind`` becomes mandatory and
the course/root, ω-range and no-self-loop rules are database constraints.
"""

import django.db.models.deletion
import tree_queries.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0011_kb_data'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='topic',
            options={'ordering': ['position', 'id'], 'verbose_name': 'Topic', 'verbose_name_plural': 'Topics'},
        ),
        migrations.RemoveField(model_name='topic', name='level'),
        migrations.RemoveField(model_name='topic', name='lft'),
        migrations.RemoveField(model_name='topic', name='rght'),
        migrations.RemoveField(model_name='topic', name='tree_id'),
        migrations.AlterField(
            model_name='topic',
            name='parent',
            field=tree_queries.fields.TreeNodeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='curriculum.topic'),
        ),
        migrations.AlterField(
            model_name='topic',
            name='kind',
            field=models.CharField(choices=[('course', 'Course'), ('section', 'Section'), ('topic', 'Topic')], db_index=True, max_length=10),
        ),
        migrations.AddConstraint(
            model_name='topic',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('kind', 'course'), ('parent__isnull', True)), models.Q(models.Q(('kind', 'course'), _negated=True), ('parent__isnull', False)), _connector='OR'), name='topic_course_is_root'),
        ),
        migrations.AddConstraint(
            model_name='topic',
            constraint=models.CheckConstraint(condition=models.Q(('kind__in', ['course', 'section', 'topic'])), name='topic_kind_valid'),
        ),
        migrations.AlterUniqueTogether(
            name='topicprerequisite',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='topicprerequisite',
            constraint=models.UniqueConstraint(fields=('topic', 'prerequisite'), name='uniq_prerequisite_edge'),
        ),
        migrations.AddConstraint(
            model_name='topicprerequisite',
            constraint=models.CheckConstraint(condition=models.Q(('topic', models.F('prerequisite')), _negated=True), name='prerequisite_not_self'),
        ),
        migrations.AddConstraint(
            model_name='topicprerequisite',
            constraint=models.CheckConstraint(condition=models.Q(('weight__gt', 0), ('weight__lte', 1)), name='prerequisite_weight_range'),
        ),
    ]

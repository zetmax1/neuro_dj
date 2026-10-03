from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('curriculum', '0008_topic_pass_mark_percentage_topic_test_question_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='is_archived',
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text='Hidden from learners and instructors; kept because answers reference it.',
            ),
        ),
    ]

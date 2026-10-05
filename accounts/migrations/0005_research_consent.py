"""
Research consent and the pseudonym (D42, D43).

``research_pseudonym`` is added in three steps rather than one. A field with a
callable default is added by evaluating that callable **once** and writing the
same value to every existing row, which a unique column rejects — and would be
wrong even if it did not, because every learner needs their own pseudonym. So
the column arrives nullable and not unique, ``assign_pseudonyms`` fills it a
row at a time, and only then does it become unique and non-null.
"""

from django.db import migrations, models

import accounts.models


def assign_pseudonyms(apps, schema_editor):
    """One fresh pseudonym per existing account, collisions retried."""
    User = apps.get_model("accounts", "CustomUser")
    taken: set[str] = set(
        User.objects.exclude(research_pseudonym=None)
        .values_list("research_pseudonym", flat=True)
    )
    rows = list(User.objects.filter(research_pseudonym=None).order_by("pk"))
    for row in rows:
        value = accounts.models.new_pseudonym()
        while value in taken:
            value = accounts.models.new_pseudonym()
        taken.add(value)
        row.research_pseudonym = value
    User.objects.bulk_update(rows, ["research_pseudonym"], batch_size=500)


def drop_pseudonyms(apps, schema_editor):
    """Reverse of the data step: the column is about to be removed anyway."""
    User = apps.get_model("accounts", "CustomUser")
    User.objects.update(research_pseudonym=None)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_user_is_simulated"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="research_consent",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="The learner agreed that their answers may be used in the thesis.",
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="research_consent_at",
            field=models.DateTimeField(
                blank=True,
                help_text="When the consent flag last changed, in either direction.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="customuser",
            name="research_pseudonym",
            field=models.CharField(
                editable=False,
                help_text="Random and irreversible; the only identifier an export carries (D43).",
                max_length=16,
                null=True,
            ),
        ),
        migrations.RunPython(assign_pseudonyms, drop_pseudonyms),
        migrations.AlterField(
            model_name="customuser",
            name="research_pseudonym",
            field=models.CharField(
                default=accounts.models.new_pseudonym,
                editable=False,
                help_text="Random and irreversible; the only identifier an export carries (D43).",
                max_length=16,
                unique=True,
            ),
        ),
    ]

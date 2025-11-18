# Generated migration to remove image field from Motor model

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="motor",
            name="image",
        ),
    ]

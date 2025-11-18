# Generated migration to add quantity field to Motor model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_remove_motor_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="motor",
            name="quantity",
            field=models.PositiveIntegerField(
                default=1, help_text="Number of units in inventory."
            ),
        ),
    ]

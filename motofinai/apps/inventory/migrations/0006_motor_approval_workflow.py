# Generated migration for motor approval workflow

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventory', '0005_alter_motor_remove_status_and_type_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='motor',
            name='approval_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending Approval'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                ],
                default='pending',
                help_text='Motorcycle approval status for financing',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='motor',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                help_text='Finance officer who approved this motorcycle',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_motors',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='motor',
            name='approved_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When this motorcycle was approved',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='motor',
            name='approval_notes',
            field=models.TextField(
                blank=True,
                help_text='Notes from the approving finance officer',
            ),
        ),
    ]

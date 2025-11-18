# Generated migration for removing Motor status field and adding type choices
# Also adding reserved and repossessed quantity fields to Stock

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_stock_motor_stock'),
    ]

    operations = [
        # Remove status field from Motor
        migrations.RemoveField(
            model_name='motor',
            name='status',
        ),
        # Alter type field to have choices and max_length 20
        migrations.AlterField(
            model_name='motor',
            name='type',
            field=models.CharField(
                choices=[
                    ('scooter', 'Scooter'),
                    ('underbone', 'Underbone'),
                    ('standard', 'Standard'),
                    ('cruiser', 'Cruiser'),
                    ('sport', 'Sport'),
                    ('touring', 'Touring'),
                    ('adventure', 'Adventure'),
                    ('moped', 'Moped'),
                    ('capping', 'Capping'),
                    ('tricycle', 'Tricycle'),
                ],
                default='scooter',
                help_text='Motorcycle category',
                max_length=20,
            ),
        ),
        # Add quantity_reserved to Stock
        migrations.AddField(
            model_name='stock',
            name='quantity_reserved',
            field=models.PositiveIntegerField(default=0),
        ),
        # Add quantity_repossessed to Stock
        migrations.AddField(
            model_name='stock',
            name='quantity_repossessed',
            field=models.PositiveIntegerField(default=0),
        ),
    ]

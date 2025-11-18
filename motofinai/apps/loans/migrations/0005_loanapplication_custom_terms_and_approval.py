# Generated migration for loan application custom terms and approval tracking

from decimal import Decimal
from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('loans', '0004_alter_paymentschedule_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='loanapplication',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                help_text='Finance officer who approved this loan',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='approved_loan_applications',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='loanapplication',
            name='custom_interest_rate',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Custom interest rate if different from financing term',
                max_digits=5,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))],
            ),
        ),
        migrations.AddField(
            model_name='loanapplication',
            name='custom_term_years',
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text='Custom loan duration in years if different from financing term',
                null=True,
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
    ]

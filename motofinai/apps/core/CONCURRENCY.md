# Concurrency Control and Consistency Documentation

This document describes the concurrency control and data consistency mechanisms implemented in the Motofinai system.

## Overview

The concurrency control system provides:

1. **Optimistic Locking** - Version-based conflict detection
2. **Consistency Checking** - Data integrity verification
3. **Transaction Safety** - Atomic multi-step operations
4. **Race Condition Detection** - Monitoring and alerting
5. **Management Commands** - System maintenance tools

## Optimistic Locking

Optimistic locking prevents lost updates when multiple users modify the same record simultaneously.

### How It Works

Each versioned record includes:
- `version` - Incremented on each update
- `last_modified_at` - Timestamp of last change

When updating:
1. Read the current version
2. Apply changes
3. Check if version matches expected version
4. If mismatch, raise `ConcurrencyException`
5. If match, increment version and save

### Usage

```python
from motofinai.apps.core.concurrency import VersionedModel, TransactionConsistency

# Updating with version checking
class Loan(VersionedModel):
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20)

# Get object for update
try:
    loan = Loan.get_for_update(Loan, loan_id, expected_version=5)
    loan.status = "approved"
    loan.save()
except ConcurrencyException as e:
    # Object was modified by another user
    # Notify user to reload and retry
    pass

# Using safe update with version
updated_loan = TransactionConsistency.safe_update_with_version(
    Loan,
    loan_id=123,
    current_version=5,
    update_fields={"status": "approved"}
)
```

### In Views

```python
from django.views import View
from django.views.decorators.http import require_http_methods
from motofinai.apps.core.exceptions import ConcurrencyException
from motofinai.apps.core.responses import APIResponse

class LoanUpdateView(View):
    @require_http_methods(["POST"])
    def post(self, request, loan_id):
        try:
            version = request.POST.get("version")

            loan = Loan.get_for_update(Loan, loan_id, expected_version=int(version))
            loan.status = "approved"
            loan.save()

            return APIResponse.success(data=loan.to_dict())
        except ConcurrencyException:
            return APIResponse.conflict(
                "The loan was modified by another user. Please refresh and try again."
            )
```

## Consistency Checking

The consistency checker verifies data integrity across related records.

### Types of Checks

#### Loan Consistency
- Motor exists
- Applicant is active
- Payment schedule total matches loan amount
- Payments don't exceed loan amount
- Completed loans are fully paid
- No overdue unpaid schedules

#### Payment Consistency
- Referenced loan exists
- Payment date is not in future
- Payment amount is reasonable vs scheduled
- Payment is not duplicated

#### Inventory Consistency
- VINs are unique
- Motor not assigned to multiple active loans
- Motor status matches assignment status

#### System Consistency
- No orphaned records
- All foreign key references valid
- No duplicate data
- All records in consistent state

### Usage Examples

```python
from motofinai.apps.core.concurrency import ConsistencyChecker

# Check specific loan
issues = ConsistencyChecker.check_loan_consistency(loan_id=123)
if issues["errors"]:
    # Handle errors
    for error in issues["errors"]:
        print(error)

# Check payment
issues = ConsistencyChecker.check_payment_consistency(payment_id=456)

# Check motor inventory
issues = ConsistencyChecker.check_inventory_consistency(motor_id=789)

# Full system check
issues = ConsistencyChecker.check_system_consistency()
print(f"Errors: {len(issues['errors'])}")
print(f"Warnings: {len(issues['warnings'])}")
```

### Response Format

```python
{
    "errors": [
        "Payment schedule total (50000) does not match loan amount (55000)",
        "Total paid (55500) exceeds loan amount (55000)"
    ],
    "warnings": [
        "Loan applicant is inactive",
        "3 payment(s) are overdue"
    ]
}
```

## Transaction Consistency

Ensures multi-step operations are atomic and consistent.

### Safe Updates

```python
from motofinai.apps.core.concurrency import TransactionConsistency

# Execute operation with consistency check
def approve_loan(loan_id):
    loan = LoanApplication.objects.get(id=loan_id)
    loan.status = "approved"
    loan.save()
    return loan

result = TransactionConsistency.execute_with_consistency_check(
    approve_loan,
    loan_id=123,
    consistency_check_func=ConsistencyChecker.check_loan_consistency
)
```

### Using Transactions

```python
from django.db import transaction
from motofinai.apps.core.concurrency import TransactionConsistency

@transaction.atomic
def process_payment(payment_id):
    payment = Payment.objects.select_for_update().get(id=payment_id)

    # Multiple operations
    payment.status = "completed"
    payment.save()

    loan = payment.loan
    loan.paid_amount += payment.amount
    loan.save()

    # If any exception occurs, all changes are rolled back
    return payment
```

## Race Condition Detection

Monitors for patterns indicating concurrent modification issues.

### Detecting Version Conflicts

```python
from motofinai.apps.core.concurrency import RaceConditionDetector
from motofinai.apps.loans.models import LoanApplication

# Find objects with high modification rates
conflicts = RaceConditionDetector.detect_version_conflicts(
    LoanApplication,
    hours=1
)

for obj in conflicts["high_version_objects"]:
    print(f"Object {obj['id']}: {obj['version']} modifications in last hour")
```

### Detecting Deadlock Patterns

```python
# Find objects being modified excessively
deadlocks = RaceConditionDetector.detect_deadlocks(LoanApplication)

if deadlocks["objects_with_high_versions"]:
    # Alert system administrators
    send_alert("High version objects detected - possible race condition")
```

## Management Commands

### Check Consistency

Run consistency checks on the system:

```bash
# Quick check (recommended for regular runs)
python manage.py check_consistency

# Check specific loan
python manage.py check_consistency --loan 123

# Check specific payment
python manage.py check_consistency --payment 456

# Check specific motor
python manage.py check_consistency --motor 789

# Full system check (may take time)
python manage.py check_consistency --all

# Verbose output
python manage.py check_consistency --all --verbose

# Attempt to fix issues (use with caution!)
python manage.py check_consistency --all --fix
```

### Example Output

```
Starting consistency checks...

Running quick consistency check...
  ✓ No issues found

==================================================
Consistency check completed
Errors found: 0
Warnings found: 0
```

With errors:

```
Starting consistency checks...

Checking loan 123...
  ✗ 2 error(s) found:
    - Payment schedule total (45000) does not match loan amount (50000)
    - Total paid (51000) exceeds loan amount (50000)

==================================================
Consistency check completed
Errors found: 2
Warnings found: 0

Run with --fix flag to attempt automatic fixes (use with caution)
```

## Implementation in Models

To add versioning to a model:

```python
from django.db import models
from motofinai.apps.core.concurrency import VersionedModel

class Loan(VersionedModel):
    """Loan with optimistic locking."""

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20)

    class Meta:
        db_table = "loans_loan"
        indexes = [
            models.Index(fields=["version", "-last_modified_at"]),
        ]
```

Migration:

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('loans', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='loan',
            name='version',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='loan',
            name='last_modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddIndex(
            model_name='loan',
            index=models.Index(fields=['version', '-last_modified_at'], name='loan_version_idx'),
        ),
    ]
```

## Error Handling

### ConcurrencyException

```python
from motofinai.apps.core.exceptions import ConcurrencyException

try:
    loan = Loan.get_for_update(Loan, loan_id, expected_version=5)
    # Update loan...
except ConcurrencyException as e:
    # Handle concurrent modification
    # Log the incident
    # Notify user
    # Request retry
    pass
```

## Best Practices

1. **Always use `select_for_update()` when checking versions**
   ```python
   obj = Model.objects.select_for_update().get(id=id)
   ```

2. **Check version before updating**
   ```python
   if obj.version != expected_version:
       raise ConcurrencyException("Object was modified")
   ```

3. **Increment version after update**
   ```python
   obj.increment_version()
   obj.save(update_fields=["field", "version"])
   ```

4. **Run consistency checks regularly**
   ```bash
   # Daily via cron
   python manage.py check_consistency
   ```

5. **Monitor for race conditions**
   ```python
   conflicts = RaceConditionDetector.detect_version_conflicts(Model, hours=1)
   if conflicts["high_version_objects"]:
       send_alert("Race condition detected")
   ```

6. **Use transactions for multi-step operations**
   ```python
   with transaction.atomic():
       # Multiple operations
       pass
   ```

## Performance Considerations

- **Version queries are indexed** - `version` field has a database index
- **Last modified tracking** - Helps identify hotspot objects
- **Consistency checks** - Use pagination for large checks
- **Lock timeouts** - Configure database-level lock timeouts

## Monitoring and Alerts

Set up monitoring for:

1. **High version numbers** - Indicates excessive modifications
2. **Consistency check failures** - Data integrity issues
3. **ConcurrencyException frequency** - Race condition hotspots
4. **Lock timeouts** - Database concurrency issues

## Troubleshooting

### "Version Mismatch" Errors

Usually caused by:
1. User takes too long to submit form (other user modifies in between)
2. Multiple tabs/browsers editing same record
3. Browser refresh clearing form state

Solutions:
1. Show current version in form
2. Refresh form before submit if changed
3. Implement form autosave with version tracking

### Slow Consistency Checks

If `check_consistency --all` is slow:
1. Use `--quick` flag for quick check
2. Check specific object with `--loan`, `--payment`, etc.
3. Schedule full check during off-hours
4. Run in background job (Celery, etc.)

### High Version Numbers

Indicates:
1. Object is being modified frequently by many users
2. Possible race condition or coordination issue
3. May need workflow redesign

Actions:
1. Review modification patterns
2. Implement request queuing
3. Add user-level locking if appropriate

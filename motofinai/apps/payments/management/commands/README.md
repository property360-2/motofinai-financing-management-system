# Payment Reminder System

This management command sends automated payment reminders to customers for upcoming and overdue payment schedules.

## Usage

### Basic Usage

```bash
python manage.py send_payment_reminders
```

This will:
- Send reminders for payments due in 3 days (default)
- Send reminders for overdue payments at intervals: 1, 7, 14, and 30 days overdue (default)

### Options

#### `--days-before <days>`
Number of days before due date to send upcoming payment reminder. Default: 3

```bash
python manage.py send_payment_reminders --days-before 5
```

#### `--overdue-intervals <intervals>`
Comma-separated list of days overdue to send reminders. Default: "1,7,14,30"

This prevents spamming customers with daily reminders. Reminders are only sent on specific days after the due date.

```bash
python manage.py send_payment_reminders --overdue-intervals "1,3,7,14,21,30"
```

#### `--dry-run`
Test the command without actually sending emails. Useful for debugging.

```bash
python manage.py send_payment_reminders --dry-run
```

### Example: Custom Configuration

```bash
python manage.py send_payment_reminders --days-before 7 --overdue-intervals "1,14,30"
```

This will:
- Send reminders 7 days before payment is due
- Send overdue reminders only on day 1, 14, and 30 after the due date

## Email Configuration

The command uses Django's email backend configured in `settings.py`:

- **Development**: Uses `console.EmailBackend` (prints emails to console)
- **Production**: Configure SMTP settings via environment variables

### Environment Variables for Production

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=noreply@dcfinancingcorp.com
```

## Scheduling

To automate payment reminders, schedule this command to run daily using your operating system's scheduler.

### Linux/Unix (cron)

Edit your crontab:
```bash
crontab -e
```

Add this line to run daily at 9:00 AM:
```cron
0 9 * * * cd /path/to/project && /path/to/venv/bin/python manage.py send_payment_reminders
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to "Daily" at desired time (e.g., 9:00 AM)
4. Action: "Start a program"
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `manage.py send_payment_reminders`
   - Start in: `C:\path\to\project`

### Using a Process Manager (Production)

For production servers, consider using Celery Beat or similar task schedulers:

```python
# celerybeat-schedule.py
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    'send-payment-reminders': {
        'task': 'payments.tasks.send_payment_reminders',
        'schedule': crontab(hour=9, minute=0),  # 9:00 AM daily
    },
}
```

## Email Template

The email template is located at:
```
motofinai/templates/emails/payment_reminder.txt
```

You can customize this template to match your organization's branding and messaging.

## How It Works

1. **Mark Overdue**: Updates payment schedules that have passed their due date to "overdue" status
2. **Find Upcoming**: Queries payment schedules due on the specified upcoming date (default: 3 days from now)
3. **Find Overdue**: Queries all overdue payment schedules
4. **Filter Intervals**: For overdue payments, only sends reminders if the number of days overdue matches one of the specified intervals
5. **Send Emails**: Sends personalized email reminders to applicants
6. **Report**: Outputs a summary of reminders sent

## Testing

Before deploying to production, test the command with dry-run:

```bash
# Test with dry-run
python manage.py send_payment_reminders --dry-run

# Test with console backend (emails printed to terminal)
# This is the default in development mode
python manage.py send_payment_reminders
```

## Best Practices

1. **Run daily**: Schedule the command to run once per day
2. **Consistent timing**: Run at a consistent time each day (e.g., 9:00 AM)
3. **Monitor logs**: Check command output for errors or delivery issues
4. **Interval spacing**: Use reasonable intervals (1, 7, 14, 30 days) to avoid spam
5. **Test first**: Always test with `--dry-run` before deploying changes

from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

from motofinai.apps.loans.models import PaymentSchedule


class Command(BaseCommand):
    help = "Send payment reminders for upcoming and overdue payment schedules"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days-before",
            type=int,
            default=3,
            help="Number of days before due date to send reminder (default: 3)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would be sent without actually sending emails",
        )
        parser.add_argument(
            "--overdue-intervals",
            type=str,
            default="1,7,14,30",
            help="Comma-separated list of days overdue to send reminders (default: 1,7,14,30)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        days_before = options["days_before"]
        dry_run = options["dry_run"]
        overdue_intervals_str = options["overdue_intervals"]
        overdue_intervals = [int(x.strip()) for x in overdue_intervals_str.split(",")]

        today = timezone.now().date()
        upcoming_date = today + timedelta(days=days_before)

        # Mark overdue schedules first
        PaymentSchedule.objects.mark_overdue(today)

        # Find upcoming payment schedules (due in X days)
        upcoming_schedules = (
            PaymentSchedule.objects.select_related(
                "loan_application",
                "loan_application__motor",
            )
            .filter(
                status=PaymentSchedule.Status.DUE,
                due_date=upcoming_date,
            )
        )

        # Find overdue payment schedules
        overdue_schedules = (
            PaymentSchedule.objects.select_related(
                "loan_application",
                "loan_application__motor",
            )
            .filter(
                status=PaymentSchedule.Status.OVERDUE,
            )
        )

        upcoming_count = 0
        overdue_count = 0

        # Send upcoming reminders
        for schedule in upcoming_schedules:
            loan = schedule.loan_application

            subject = f"Payment Reminder: Installment #{schedule.sequence} Due Soon"
            context = {
                "applicant_name": f"{loan.applicant_first_name} {loan.applicant_last_name}",
                "sequence": schedule.sequence,
                "due_date": schedule.due_date,
                "amount": schedule.total_amount,
                "motor_model": loan.motor.model if loan.motor else "N/A",
                "days_until_due": days_before,
                "is_overdue": False,
            }

            message = render_to_string("emails/payment_reminder.txt", context)

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"[DRY RUN] Would send upcoming reminder to {loan.applicant_email} "
                        f"for schedule #{schedule.sequence}"
                    )
                )
            else:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[loan.applicant_email],
                    fail_silently=False,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Sent upcoming reminder to {loan.applicant_email} "
                        f"for schedule #{schedule.sequence}"
                    )
                )

            upcoming_count += 1

        # Send overdue reminders (only at specified intervals)
        for schedule in overdue_schedules:
            loan = schedule.loan_application
            days_overdue = (today - schedule.due_date).days

            # Only send reminder if days overdue matches one of the intervals
            if days_overdue not in overdue_intervals:
                continue

            subject = f"URGENT: Overdue Payment - Installment #{schedule.sequence}"
            context = {
                "applicant_name": f"{loan.applicant_first_name} {loan.applicant_last_name}",
                "sequence": schedule.sequence,
                "due_date": schedule.due_date,
                "amount": schedule.total_amount,
                "motor_model": loan.motor.model if loan.motor else "N/A",
                "days_overdue": days_overdue,
                "is_overdue": True,
            }

            message = render_to_string("emails/payment_reminder.txt", context)

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY RUN] Would send overdue reminder to {loan.applicant_email} "
                        f"for schedule #{schedule.sequence} ({days_overdue} days overdue)"
                    )
                )
            else:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[loan.applicant_email],
                    fail_silently=False,
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"Sent overdue reminder to {loan.applicant_email} "
                        f"for schedule #{schedule.sequence} ({days_overdue} days overdue)"
                    )
                )

            overdue_count += 1

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'[DRY RUN] ' if dry_run else ''}Payment Reminder Summary:"
            )
        )
        self.stdout.write(f"  - Upcoming reminders: {upcoming_count}")
        self.stdout.write(f"  - Overdue reminders: {overdue_count}")
        self.stdout.write(f"  - Total: {upcoming_count + overdue_count}")

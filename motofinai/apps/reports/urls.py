"""URL routing for reports system."""

from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportListView.as_view(), name="list"),
    path("dashboard/", views.ComprehensiveReportsDashboardView.as_view(), name="comprehensive-dashboard"),
    path("applicants/", views.ApplicantsReportView.as_view(), name="applicants"),
    path("approved-loans/", views.ApprovedLoansReportView.as_view(), name="approved_loans"),
    path("released-motors/", views.ReleasedMotorsReportView.as_view(), name="released_motors"),
    path("ongoing-loans/", views.OngoingLoansReportView.as_view(), name="ongoing_loans"),
    path("motorcycle-status/", views.MotorcycleStatusReportView.as_view(), name="motorcycle_status"),
    path("payment-reconciliation/", views.PaymentReconciliationReportView.as_view(), name="payment_reconciliation"),
]

from django.urls import path

from .views import (
    LoanRiskEvaluateView,
    RiskAssessmentDashboardView,
    RiskAssessmentDetailView,
    RiskAssessmentRecalculateView,
)

app_name = "risk"

urlpatterns = [
    path("", RiskAssessmentDashboardView.as_view(), name="dashboard"),
    path("loans/<int:loan_pk>/evaluate/", LoanRiskEvaluateView.as_view(), name="evaluate-loan"),
    path("<int:pk>/", RiskAssessmentDetailView.as_view(), name="detail"),
    path("<int:pk>/recalculate/", RiskAssessmentRecalculateView.as_view(), name="recalculate"),
]

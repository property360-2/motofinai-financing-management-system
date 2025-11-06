"""
Dashboard URL Configuration
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('admin/', views.AdminDashboardView.as_view(), name='admin'),
    path('finance/', views.FinanceDashboardView.as_view(), name='finance'),
    path('loan-officer/', views.LoanOfficerDashboardView.as_view(), name='loan_officer'),

    # Export endpoints
    path('export/loans/', views.ExportLoansView.as_view(), name='export_loans'),
    path('export/payments/', views.ExportPaymentsView.as_view(), name='export_payments'),
    path('export/risk/', views.ExportRiskView.as_view(), name='export_risk'),
    path('export/inventory/', views.ExportInventoryView.as_view(), name='export_inventory'),
]

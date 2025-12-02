from django.urls import path

from .views import (
    LoanApplicationActivateView,
    LoanApplicationApproveView,
    LoanApplicationCompleteView,
    LoanApplicationDetailView,
    LoanApplicationDocumentsView,
    LoanApplicationExportView,
    LoanApplicationListView,
    LoanApplicationWizard,
    LoanDocumentDeleteView,
)

app_name = "loans"

urlpatterns = [
    path("", LoanApplicationListView.as_view(), name="list"),
    path("export/", LoanApplicationExportView.as_view(), name="export"),
    path("new/", LoanApplicationWizard.as_view(), name="new"),
    path("<int:pk>/", LoanApplicationDetailView.as_view(), name="detail"),
    path("<int:pk>/documents/", LoanApplicationDocumentsView.as_view(), name="documents"),
    path("<int:pk>/approve/", LoanApplicationApproveView.as_view(), name="approve"),
    path("<int:pk>/activate/", LoanApplicationActivateView.as_view(), name="activate"),
    path("<int:pk>/complete/", LoanApplicationCompleteView.as_view(), name="complete"),
    path(
        "<int:pk>/documents/<int:document_pk>/delete/",
        LoanDocumentDeleteView.as_view(),
        name="document-delete",
    ),
]

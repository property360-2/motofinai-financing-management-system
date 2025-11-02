from django.urls import path

from .views import (
    RepossessionCaseDetailView,
    RepossessionCaseListView,
    RepossessionCaseCloseView,
    RepossessionCaseReminderView,
)

app_name = "repossession"

urlpatterns = [
    path("", RepossessionCaseListView.as_view(), name="case-list"),
    path("<int:pk>/", RepossessionCaseDetailView.as_view(), name="case-detail"),
    path("<int:pk>/remind/", RepossessionCaseReminderView.as_view(), name="send-reminder"),
    path("<int:pk>/close/", RepossessionCaseCloseView.as_view(), name="close-case"),
]

from django.urls import path

from .views import (
    UserCreateView,
    UserDetailView,
    UserListView,
    UserLoginView,
    UserLogoutView,
    UserUpdateView,
)


app_name = "users"

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("manage/", UserListView.as_view(), name="user-list"),
    path("manage/create/", UserCreateView.as_view(), name="user-create"),
    path("manage/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("manage/<int:pk>/edit/", UserUpdateView.as_view(), name="user-edit"),
]

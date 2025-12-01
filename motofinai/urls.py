"""
URL configuration for DC Financing Corporation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("", include("motofinai.apps.users.urls")),
    path("dashboard/", include("motofinai.apps.dashboard.urls")),
    path("inventory/", include("motofinai.apps.inventory.urls")),
    path("terms/", include("motofinai.apps.loans.urls")),
    path("loans/", include("motofinai.apps.loans.urls_applications")),
    path("payments/", include("motofinai.apps.payments.urls")),
    path("pos/", include("motofinai.apps.pos.urls")),
    path("reports/", include("motofinai.apps.reports.urls")),
    path("risk/", include("motofinai.apps.risk.urls")),
    path("repos/", include("motofinai.apps.repossession.urls")),
    path("audit/", include("motofinai.apps.audit.urls")),
    path("archive/", include("motofinai.apps.archive.urls")),
]

from django.contrib import admin
from django.urls import include,path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Django login, logout, and password-management routes
    path("accounts/", include("django.contrib.auth.urls")),

    # Application routes, including home and pantry operations
    path("", include("core.urls")),
]
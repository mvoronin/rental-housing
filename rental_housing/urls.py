from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.views.i18n import set_language

urlpatterns = [
    path("", RedirectView.as_view(url="/leases/", permanent=False)),
    path("admin/", admin.site.urls),
    path("leases/", include("leases.urls")),
    path("i18n/setlang/", set_language, name="set_language"),
]

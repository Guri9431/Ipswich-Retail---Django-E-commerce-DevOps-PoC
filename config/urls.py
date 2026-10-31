from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Prometheus scrape endpoint -> /metrics
    path("", include("django_prometheus.urls")),
    path("", include("store.urls")),
]

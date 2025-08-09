from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    # OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    # Apps
    path("api/users/", include("users.urls")),
    path("api/auth/", include("users.auth_urls")),
    path("api/frameworks/", include("frameworks.urls")),
    path("api/responses/", include("responses.urls")),
    path("api/", include("assessments.urls")),
    path("api/", include("recommendations.urls")),
    path("api/planos/", include("actionplans.urls")),
]

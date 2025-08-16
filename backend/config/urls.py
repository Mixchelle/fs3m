from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Projeto FS3M",
        default_version="v1",
        description="Documentação da API para a CyberSec Maturity Platform",
        terms_of_service="https://www.seusite.com/terms/",
        contact=openapi.Contact(email="suporte@seusite.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Swagger/Redoc (drf-yasg)
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),

    # APIs
    path("api/users/", include("users.urls")),
    path("api/auth/", include("users.auth_urls")),
    path("api/frameworks/", include("frameworks.urls")),
    path("api/responses/", include("responses.urls")),
    path("api/", include("assessments.urls")),
    path("api/", include("recommendations.urls")),
    path("api/planos/", include("actionplans.urls")),
]

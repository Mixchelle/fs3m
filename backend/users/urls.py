# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MeView, UserViewSet

router = DefaultRouter()
router.register("", UserViewSet, basename="user")

urlpatterns = [
    path("me/", MeView.as_view(), name="auth_me"),  # /api/users/me/
    path("", include(router.urls)),                 # /api/users/ e /api/users/<id>/
]

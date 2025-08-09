# users/auth_urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import CustomTokenObtainPairView, LogoutAndBlacklistRefreshTokenForUserView, MeView

urlpatterns = [
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("logout/", LogoutAndBlacklistRefreshTokenForUserView.as_view(), name="token_blacklist"),
    path("me/", MeView.as_view(), name="auth_me"),
]

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView,
    RequestOTPView,
    VerifyOTPView,
    LogoutView,
    UserProfileView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("otp/request/", RequestOTPView.as_view(), name="otp_request"),
    path("otp/vefiry/", VerifyOTPView.as_view(), name="otp_verify"),
    # =======================================================================
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # =======================================================================
    path("me/", UserProfileView.as_view(), name="user_profile"),
]

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView,
    PasswordLoginView,
    QuickOTPRequestView,
    VerifyOTPView,
    ForgotPasswordRequestView,
    ResetPasswordConfirmView,
    LogoutView,
    UserProfileView,
)

urlpatterns = [
    # ثبت‌نام
    path("register/", RegisterView.as_view(), name="register"),
    # ورود با پسورد
    path("login/", PasswordLoginView.as_view(), name="login_password"),
    # ورود سریع با OTP
    path("quick-otp/", QuickOTPRequestView.as_view(), name="quick_otp"),
    # تایید کد همه‌منظوره (ثبت‌نام و ورود سریع)
    path("otp/verify/", VerifyOTPView.as_view(), name="otp_verify"),
    # بازیابی پسورد
    path(
        "password-reset/request/",
        ForgotPasswordRequestView.as_view(),
        name="forgot_password_request",
    ),
    path(
        "password-reset/confirm/",
        ResetPasswordConfirmView.as_view(),
        name="forgot_password_confirm",
    ),
    # توکن و خروج
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # پروفایل
    path("me/", UserProfileView.as_view(), name="user_profile"),
]

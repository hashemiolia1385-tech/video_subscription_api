from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import OTPRequest
from .serializers import (
    FullRegisterSerializer,
    PasswordLoginSerializer,
    QuickOTPRequestSerializer,
    GeneralOTPVerifySerializer,
    ResetPasswordSerializer,
    UserProfileSerializer,
)

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = FullRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # ارسال خودکار OTP به ایمیل یا تلفن وارد شده
        ident = serializer.validated_data["identifier"]
        OTPRequest.generate_otp(identifier=ident)
        channel_name = "ایمیل" if "@" in ident else "شماره تلفن"

        return Response(
            {
                "detail": f"کد تایید برای {channel_name} شما ارسال شد.",
                "identifier": ident,
                "channel": "email" if "@" in ident else "phone",
            },
            status=status.HTTP_201_CREATED,
        )


class PasswordLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "detail": "ورود موفقیت‌آمیز بود.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_200_OK,
        )


class QuickOTPRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = QuickOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ident = serializer.validated_data["identifier"]

        OTPRequest.generate_otp(identifier=ident)
        channel_name = "ایمیل" if "@" in ident else "شماره تلفن"

        return Response(
            {
                "detail": f"کد تایید سریع برای {channel_name} شما ارسال شد.",
                "identifier": ident,
                "channel": "email" if "@" in ident else "phone",
            },
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GeneralOTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ident = serializer.validated_data["identifier"]
        code = serializer.validated_data["code"]

        otp_record = (
            OTPRequest.objects.filter(identifier=ident, code=code, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp_record or not otp_record.is_valid():
            return Response(
                {"detail": "کد تایید اشتباه یا منقضی شده است."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_record.is_used = True
        otp_record.save()

        # فعال‌سازی کاربر در صورت وجود
        user = User.objects.filter(
            Q(email__iexact=ident) | Q(phone_number=ident)
        ).first()

        if user:
            if not user.is_active:
                user.is_active = True
                user.save()
        else:
            # ایجاد سریع کاربر در صورت نیاز
            user = User.objects.create(
                phone_number=ident if "@" not in ident else None,
                email=ident if "@" in ident else "",
                username=f"user_{ident.replace('@', '_').replace('.', '_')}",
                is_active=True,
            )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "detail": "ورود موفقیت‌آمیز بود.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            },
            status=status.HTTP_200_OK,
        )


class ForgotPasswordRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = QuickOTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ident = serializer.validated_data["identifier"]

        OTPRequest.generate_otp(identifier=ident)
        channel_name = "ایمیل" if "@" in ident else "شماره همراه"

        return Response(
            {
                "detail": f"کد بازیابی رمز برای {channel_name} شما ارسال شد.",
                "identifier": ident,
                "channel": "email" if "@" in ident else "phone",
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ident = serializer.validated_data["identifier"]
        code = serializer.validated_data["code"]
        new_pwd = serializer.validated_data["new_password"]

        otp_record = (
            OTPRequest.objects.filter(identifier=ident, code=code, is_used=False)
            .order_by("-created_at")
            .first()
        )

        if not otp_record or not otp_record.is_valid():
            return Response(
                {"detail": "کد اعتبارسنجی نامعتبر یا منقضی است."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp_record.is_used = True
        otp_record.save()

        user = User.objects.filter(
            Q(email__iexact=ident) | Q(phone_number=ident)
        ).first()
        if not user:
            return Response(
                {"detail": "کاربر پیدا نشد."}, status=status.HTTP_404_NOT_FOUND
            )

        user.set_password(new_pwd)
        user.save()

        return Response(
            {"detail": "رمز عبور با موفقیت به‌روزرسانی شد. اکنون وارد شوید."},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "ارسال رفرش توکن الزامی است."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"detail": "خروج با موفقیت انجام شد."}, status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {"detail": "توکن نامعتبر است."}, status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

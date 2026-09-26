import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q

User = get_user_model()


def clean_identifier(value):
    val = value.strip()
    if "@" in val:
        # ولیدیشن ایمیل
        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_regex, val):
            raise serializers.ValidationError("فرمت ایمیل وارد شده نامعتبر است.")
        return val.lower()
    else:
        # ولیدیشن شماره موبایل
        if not re.match(r"^09\d{9}$", val):
            raise serializers.ValidationError(
                "شماره موبایل باید ۱۱ رقم و با 09 شروع شود."
            )
        return val


class FullRegisterSerializer(serializers.ModelSerializer):
    identifier = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "identifier",
            "password",
            "password_confirm",
        ]

    def validate_identifier(self, value):
        ident = clean_identifier(value)
        if "@" in ident:
            if User.objects.filter(email=ident).exists():
                raise serializers.ValidationError(
                    "حساب کاربری با این ایمیل قبلاً ثبت شده است."
                )
        else:
            if User.objects.filter(phone_number=ident).exists():
                raise serializers.ValidationError(
                    "حساب کاربری با این شماره موبایل قبلاً ثبت شده است."
                )
        return ident

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "رمز عبور و تکرار آن یکسان نیستند."}
            )
        return attrs

    def create(self, validated_data):
        ident = validated_data.pop("identifier")
        validated_data.pop("password_confirm")

        email = ident if "@" in ident else ""
        phone = ident if "@" not in ident else None

        user = User.objects.create_user(
            username=validated_data["username"],
            email=email,
            phone_number=phone,
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            is_active=False,  # کاربر بعد از تایید OTP فعال می‌شود
        )
        return user


class PasswordLoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        ident = attrs.get("identifier").strip()
        pwd = attrs.get("password")

        # جستجو بر اساس username، email یا phone_number
        user = User.objects.filter(
            Q(username__iexact=ident) | Q(email__iexact=ident) | Q(phone_number=ident)
        ).first()

        if not user or not user.check_password(pwd):
            raise serializers.ValidationError(
                "نام کاربری/ایمیل/شماره یا رمز عبور اشتباه است."
            )

        attrs["user"] = user
        return attrs


class QuickOTPRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)

    def validate_identifier(self, value):
        ident = clean_identifier(value)
        exists = User.objects.filter(
            Q(email__iexact=ident) | Q(phone_number=ident)
        ).exists()
        if not exists:
            raise serializers.ValidationError(
                "حساب کاربری با این مشخصات یافت نشد. لطفاً ابتدا ثبت‌نام کنید."
            )
        return ident


class GeneralOTPVerifySerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    code = serializers.CharField(max_length=6, min_length=6, required=True)

    def validate_identifier(self, value):
        return clean_identifier(value)


class ResetPasswordSerializer(serializers.Serializer):
    identifier = serializers.CharField(required=True)
    code = serializers.CharField(max_length=6, min_length=6, required=True)
    new_password = serializers.CharField(
        required=True, write_only=True, validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate_identifier(self, value):
        return clean_identifier(value)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password": "تکرار رمز عبور جدید یکسان نیست."}
            )
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    wallet_balance = serializers.DecimalField(
        12, 2, source="wallet.balance", read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "wallet_balance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "username",
            "wallet_balance",
            "created_at",
            "updated_at",
        ]

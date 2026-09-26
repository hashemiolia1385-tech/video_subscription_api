import random
import re
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username or str(self.phone_number) or str(self.email)


class OTPRequest(models.Model):
    class ChannelType(models.TextChoices):
        PHONE = "phone", "Phone Number"
        EMAIL = "email", "Email Address"

    identifier = models.CharField(max_length=150, db_index=True)
    channel = models.CharField(
        max_length=10, choices=ChannelType.choices, default=ChannelType.PHONE
    )
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def detect_channel(cls, identifier: str) -> str:
        ident = identifier.strip()
        if "@" in ident:
            return cls.ChannelType.EMAIL
        return cls.ChannelType.PHONE

    @classmethod
    def generate_otp(cls, identifier: str, valid_minutes=2):
        ident = identifier.strip()
        channel = cls.detect_channel(ident)
        otp_code = f"{random.randint(100000, 999999)}"
        expiration = timezone.now() + timedelta(minutes=valid_minutes)

        cls.objects.filter(identifier=ident, is_used=False).update(is_used=True)

        otp_obj = cls.objects.create(
            identifier=ident,
            channel=channel,
            code=otp_code,
            expires_at=expiration,
        )

        label = "Email" if channel == cls.ChannelType.EMAIL else "SMS"
        print(f"\n==========================================")
        print(f" [VINORA OTP] [{label}] To: {ident} | Code: {otp_code}")
        print(f"==========================================\n")

        return otp_obj

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"OTP for {self.identifier} ({self.code})"

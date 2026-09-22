import random
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


class OTPRequest(models.Model):
    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    @classmethod
    def generate_otp(cls, phone_number, valid_minutes=2):

        otp_code = f"{random.randint(100000,999999)}"
        expiration = timezone.now() + timedelta(minutes=valid_minutes)

        cls.objects.filter(phone_number=phone_number, is_used=False).update(
            is_used=True
        )

        otp_obj = cls.objects.create(
            phone_number=phone_number, code=otp_code, expires_at=expiration
        )

        print(f"\n==========================================")
        print(f" [MOCK OTP] Phone: {phone_number} | Code: {otp_code}")
        print(f"==========================================\n")

        return otp_obj

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"OTP for {self.phone_number} ({self.code})"

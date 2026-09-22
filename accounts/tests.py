from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model
from payments.models import Wallet
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from .models import OTPRequest

User = get_user_model()


class UserWalletSignalTest(TestCase):
    def test_wallet_created_automatically_on_user_creation(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="securepassword123",
        )

        self.assertTrue(hasattr(user, "wallet"))
        self.assertIsInstance(user.wallet, Wallet)
        self.assertEqual(user.wallet.balance, 0)


class UserRegistrationAPITest(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.valid_payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Strong@Password123!",
            "password_confirm": "Strong@Password123!",
        }

    def test_successful_registration(self):
        response = self.client.post(
            self.register_url,
            self.valid_payload,
            formt="json",
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(User.objects.count(), 1)

        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.check_password("Strong@Password123!"))
        self.assertTrue(hasattr(user, "wallet"))

    def test_registration_password_mismatch(self):
        payload = self.valid_payload.copy()
        payload["password_confirm"] = "DiffrentPassword123!"
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_registration_duplicte_username(self):
        User.objects.create_user(
            username="newuser",
            email="existin@example.com",
            password="Strong@Password123!",
        )
        response = self.client.post(
            self.register_url,
            self.valid_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)


class OTPAuthenticationAPITest(APITestCase):
    def setUp(self):
        self.request_url = reverse("otp_request")
        self.verify_url = reverse("otp_verify")
        self.phone = "09123456789"

    def test_request_otp_success(self):
        response = self.client.post(
            self.request_url,
            {"phone_number": self.phone},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(OTPRequest.objects.filter(phone_number=self.phone).exists())

    def test_request_otp_invalid_phone(self):
        response = self.client.post(
            self.request_url,
            {"phone_number": "12345"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_successful_and_creates_user_with_wallet(self):
        self.client.post(
            self.request_url,
            {"phone_number": self.phone},
            format="json",
        )
        otp = OTPRequest.objects.filter(phone_number=self.phone).latest("created_at")

        response = self.client.post(
            self.verify_url,
            {"phone_number": self.phone, "code": otp.code},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        user = User.objects.get(phone_number=self.phone)
        self.assertTrue(hasattr(user, "wallet"))

    def test_verify_otp_invalid_code(self):
        self.client.post(
            self.request_url,
            {"phone_number": self.phone},
            format="json",
        )
        response = self.client.post(
            self.verify_url,
            {"phone_number": self.phone, "code": "000000"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_otp_expired_code(self):
        otp = OTPRequest.generate_otp(self.phone)

        otp.expires_at = timezone.now() - timedelta(minutes=5)
        otp.save()

        response = self.client.post(
            self.verify_url,
            {"phone_number": self.phone, "code": otp.code},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JWTAuthenticationAPITest(APITestCase):
    def setUp(self):
        self.username = "jwtuser"
        self.password = "StrongPassword123!"
        self.user = User.objects.create_user(
            username=self.username, password=self.password, email="jwtuser@example.com"
        )
        self.token_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")
        self.logout_url = reverse("logout")

    def test_obtain_token_pair_success(self):
        payload = {"username": self.username, "password": self.password}
        response = self.client.post(self.token_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_obtain_token_invalid_credentials(self):
        payload = {"username": self.username, "password": "WrongPassword"}
        response = self.client.post(self.token_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_success(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(
            self.refresh_url, {"refresh": str(refresh)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_logout_and_blacklist_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token

        # هدر احراز هویت کاربر لاگین‌شده
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        # لاگ‌اوت
        response = self.client.post(
            self.logout_url, {"refresh": str(refresh)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # تلاش برای استفاده مجدد از رفرش توکن بلک‌لیست‌شده باید با شکست روبرو شود
        refresh_attempt = self.client.post(
            self.refresh_url, {"refresh": str(refresh)}, format="json"
        )
        self.assertEqual(refresh_attempt.status_code, status.HTTP_401_UNAUTHORIZED)(
            APITestCase
        )

    def setUp(self):
        self.username = "jwtuser"
        self.password = "StrongPassword123!"
        self.user = User.objects.create_user(
            username=self.username, password=self.password, email="jwtuser@example.com"
        )
        self.token_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")
        self.logout_url = reverse("logout")

    def test_obtain_token_pair_success(self):
        payload = {"username": self.username, "password": self.password}
        response = self.client.post(self.token_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_obtain_token_invalid_credentials(self):
        payload = {"username": self.username, "password": "WrongPassword"}
        response = self.client.post(self.token_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_success(self):
        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(
            self.refresh_url, {"refresh": str(refresh)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_logout_and_blacklist_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token

        # هدر احراز هویت کاربر لاگین‌شده
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        # لاگ‌اوت
        response = self.client.post(
            self.logout_url, {"refresh": str(refresh)}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # تلاش برای استفاده مجدد از رفرش توکن بلک‌لیست‌شده باید با شکست روبرو شود
        refresh_attempt = self.client.post(
            self.refresh_url, {"refresh": str(refresh)}, format="json"
        )
        self.assertEqual(refresh_attempt.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileAPITest(APITestCase):
    def setUp(self):
        self.profile_url = reverse("user_profile")
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="StrongPassword123!",
            first_name="Ali",
        )
        # تنظیم موجودی تستی روی کیف پول خودکار ایجاد شده
        self.user.wallet.balance = 50000.00
        self.user.wallet.save()

    def test_unauthenticated_user_cannot_access_profile(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_authenticated_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(float(response.data["wallet_balance"]), 50000.00)

    def test_update_profile_success(self):
        self.client.force_authenticate(user=self.user)
        update_data = {"first_name": "UpdatedName", "email": "newemail@example.com"}
        response = self.client.patch(self.profile_url, update_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "UpdatedName")
        self.assertEqual(self.user.email, "newemail@example.com")

    def test_cannot_update_read_only_fields(self):
        self.client.force_authenticate(user=self.user)
        malicious_data = {"wallet_balance": 9999999.00, "username": "hacked_username"}
        self.client.patch(self.profile_url, malicious_data, format="json")

        self.user.refresh_from_db()
        self.user.wallet.refresh_from_db()
        # مقادیر فقط‌خواندنی نباید دستکاری شوند
        self.assertEqual(self.user.username, "profileuser")
        self.assertEqual(self.user.wallet.balance, 50000.00)

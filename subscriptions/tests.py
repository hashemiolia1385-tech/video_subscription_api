from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from payments.models import Transaction, Wallet
from .models import SubscriptionPlan, Subscription

User = get_user_model()


class SubscriptionPlanAPITest(APITestCase):
    def setUp(self):
        self.list_url = reverse("subscription-plan-list")
        self.regular_user = User.objects.create_user(
            username="regular_user", password="Password123!"
        )
        self.admin_user = User.objects.create_superuser(
            username="admin_user", password="Password123!", email="admin@example.com"
        )
        self.plan_payload = {
            "name": "پلن تستی جدید",
            "price": "150000.00",
            "duration_days": 45,
            "description": "توضیحات پلن تستی",
        }

    def test_anonymous_and_regular_user_can_list_plans(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 3)

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_create_plan(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(self.list_url, self.plan_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user_can_create_plan(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(self.list_url, self.plan_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SubscriptionPlan.objects.filter(name="پلن تستی جدید").exists())


class PurchaseSubscriptionAPITest(APITestCase):
    def setUp(self):
        self.purchase_url = reverse("subscription-purchase")
        self.user = User.objects.create_user(
            username="buyer_user", password="Password123!"
        )
        self.plan = SubscriptionPlan.objects.create(
            name="پلن یک ماهه ویژه",
            price=100000.00,
            duration_days=30,
            description="پلن تست خرید",
        )

    def test_purchase_fails_due_to_insufficient_balance(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.purchase_url, {"plan_id": self.plan.id}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("موجودی", response.data["detail"])

    def test_successful_purchase_creates_subscription_and_transaction(self):
        self.user.wallet.balance = 150000.00
        self.user.wallet.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.purchase_url,
            {"plan_id": self.plan.id, "auto_renew": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Subscription.Status.ACTIVE)
        self.assertTrue(response.data["auto_renew"])

        self.user.wallet.refresh_from_db()
        self.assertEqual(self.user.wallet.balance, 50000.00)

        self.assertEqual(Transaction.objects.filter(wallet=self.user.wallet).count(), 1)
        tx = Transaction.objects.first()
        self.assertEqual(tx.type, Transaction.Type.PAYMENT)
        self.assertEqual(tx.status, Transaction.Status.SUCCESS)

    def test_purchase_extends_existing_active_subscription(self):
        now = timezone.now()
        initial_sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=now - timedelta(days=20),
            end_date=now + timedelta(days=10),
            status=Subscription.Status.ACTIVE,
        )

        self.user.wallet.balance = 200000.00
        self.user.wallet.save()

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.purchase_url, {"plan_id": self.plan.id}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        initial_sub.refresh_from_db()
        expected_approx_end = now + timedelta(days=40)
        time_diff = abs((initial_sub.end_date - expected_approx_end).total_seconds())
        self.assertLess(time_diff, 10)


class MySubscriptionAPITest(APITestCase):
    def setUp(self):
        self.my_sub_url = reverse("my-subscription")
        self.history_url = reverse("subscription-history")
        self.user = User.objects.create_user(
            username="history_user",
            password="Password123!",
        )
        self.plan = SubscriptionPlan.objects.create(
            name="پلن یک ماهه استاندارد",
            price=99000.00,
            duration_days=30,
            description="تست تاریخچه",
        )

    def test_user_without_subscription(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.my_sub_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["has_active_subscription"])

    def test_user_with_active_subscription(self):
        now = timezone.now()
        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=now,
            end_date=now + timedelta(days=25),
            status=Subscription.Status.ACTIVE,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.my_sub_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_active_subscription"])
        self.assertTrue(response.data["is_valid"])
        self.assertGreaterEqual(response.data["days_left"], 24)

    def test_subscription_history_list(self):
        now = timezone.now()

        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=now - timedelta(days=60),
            end_date=now - timedelta(days=30),
            status=Subscription.Status.EXPIRED,
        )

        Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=now,
            end_date=now + timedelta(days=30),
            status=Subscription.Status.ACTIVE,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)


class SubscriptionActionsAPITest(APITestCase):
    def setUp(self):
        self.cancel_url = reverse("subscription-cancel")
        self.toggle_url = reverse("subscription-toggle-auto-renew")
        self.user = User.objects.create_user(
            username="action_user", password="Password123!"
        )
        self.plan = SubscriptionPlan.objects.create(
            name="پلن یک ماهه لغو",
            price=99000.00,
            duration_days=30,
            description="پلن تست اکشن‌ها",
        )

    def test_cancel_subscription_success(self):
        now = timezone.now()
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=now,
            end_date=now + timedelta(days=20),
            status=Subscription.Status.ACTIVE,
            auto_renew=True,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        sub.refresh_from_db()
        self.assertEqual(sub.status, Subscription.Status.CANCELLED)
        self.assertFalse(sub.auto_renew)

    def test_cancel_without_active_subscription_fails(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.cancel_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_toggle_auto_renew_switches_boolean(self):
        now = timezone.now()
        sub = Subscription.objects.create(
            user=self.user,
            plan=self.plan,
            start_date=now,
            end_date=now + timedelta(days=15),
            status=Subscription.Status.ACTIVE,
            auto_renew=False,
        )

        self.client.force_authenticate(user=self.user)

        response1 = self.client.post(self.toggle_url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertTrue(response1.data["auto_renew"])
        sub.refresh_from_db()
        self.assertTrue(sub.auto_renew)

        response2 = self.client.post(self.toggle_url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertFalse(response2.data["auto_renew"])
        sub.refresh_from_db()
        self.assertFalse(sub.auto_renew)

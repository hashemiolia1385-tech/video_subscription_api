from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .models import Wallet, Transaction

User = get_user_model()


class WalletAPITest(APITestCase):
    def setUp(self):
        self.wallet_url = reverse("wallet-detail")
        self.user = User.objects.create_user(
            username="wallet_user", password="Password123!"
        )

    def test_unauthenticated_user_cannot_access_wallet(self):
        response = self.client.get(self.wallet_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_retrieve_wallet(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        wallet = self.user.wallet
        wallet.balance = 250000.00
        wallet.save()

        response = self.client.get(self.wallet_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("balance", response.data)
        self.assertEqual(float(response.data["balance"]), 250000.00)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)


class DepositPaymentAPITest(APITestCase):
    def setUp(self):
        self.request_url = reverse("deposit-request")
        self.verify_url = reverse("deposit-verify")
        self.user = User.objects.create_user(
            username="deposit_user", password="Password123!"
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    def test_request_deposit_creates_pending_transaction(self):
        payload = {"amount": "150000.00"}
        response = self.client.post(self.request_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("transaction_id", response.data)

        tx = Transaction.objects.get(id=response.data["transaction_id"])
        self.assertEqual(tx.status, Transaction.Status.PENDING)
        self.assertEqual(tx.type, Transaction.Type.DEPOSIT)
        self.assertEqual(float(tx.amount), 150000.00)

    def test_verify_deposit_success_updates_wallet_balance(self):
        tx = Transaction.objects.create(
            wallet=self.user.wallet,
            amount=200000.00,
            type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.PENDING,
        )

        response = self.client.post(
            self.verify_url, {"transaction_id": tx.id, "success": True}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tx.refresh_from_db()
        self.user.wallet.refresh_from_db()

        self.assertEqual(tx.status, Transaction.Status.SUCCESS)
        self.assertEqual(float(self.user.wallet.balance), 200000.00)

    def test_verify_deposit_failed_does_not_change_balance(self):
        tx = Transaction.objects.create(
            wallet=self.user.wallet,
            amount=50000.00,
            type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.PENDING,
        )

        response = self.client.post(
            self.verify_url, {"transaction_id": tx.id, "success": False}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        tx.refresh_from_db()
        self.user.wallet.refresh_from_db()

        self.assertEqual(tx.status, Transaction.Status.FAILED)
        self.assertEqual(float(self.user.wallet.balance), 0.00)

    def test_cannot_verify_already_processed_transaction(self):
        tx = Transaction.objects.create(
            wallet=self.user.wallet,
            amount=50000.00,
            type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.SUCCESS,
        )

        response = self.client.post(
            self.verify_url, {"transaction_id": tx.id, "success": True}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TransactionHistoryAPITest(APITestCase):
    def setUp(self):
        self.history_url = reverse("transaction-history")
        self.user = User.objects.create_user(
            username="history_tx_user", password="Password123!"
        )
        self.other_user = User.objects.create_user(
            username="other_tx_user", password="Password123!"
        )

        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        Transaction.objects.create(
            wallet=self.user.wallet,
            amount=100000.00,
            type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.SUCCESS,
            description="شارژ تستی",
        )
        Transaction.objects.create(
            wallet=self.user.wallet,
            amount=50000.00,
            type=Transaction.Type.PAYMENT,
            status=Transaction.Status.SUCCESS,
            description="پرداخت تستی",
        )
        Transaction.objects.create(
            wallet=self.user.wallet,
            amount=20000.00,
            type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.PENDING,
            description="در انتظار",
        )

        Transaction.objects.create(
            wallet=self.other_user.wallet,
            amount=999999.00,
            type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.SUCCESS,
            description="تراکنش کاربر دیگر",
        )

    def test_get_transaction_history_only_returns_own_records(self):
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_filter_transactions_by_type(self):
        response = self.client.get(f"{self.history_url}?type=payment")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["type"], "payment")

    def test_filter_transactions_by_status(self):
        response = self.client.get(f"{self.history_url}?status=pending")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "pending")

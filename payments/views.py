from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework import status
from django.db import transaction
from .models import Wallet, Transaction
from .serializers import (
    WalletSerializer,
    DepositRequestSerializer,
    DepositVerifySerializer,
    TransactionSerializer,
)


class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DepositRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        amount = serializer.validated_data["amount"]
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        # ساخت تراکنش در حالت انتظار
        tx = Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            type=Transaction.Type.DEPOSIT,
            status=Transaction.Status.PENDING,
            description="درخواست شارژ آنلاین کیف‌پول",
        )

        return Response(
            {
                "detail": "درخواست پرداخت ثبت شد.",
                "transaction_id": tx.id,
                "amount": str(tx.amount),
                "payment_gateway_url": f"/api/payments/deposit/verify/?transaction_id={tx.id}",
            },
            status=status.HTTP_201_CREATED,
        )


class DepositVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DepositVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tx_id = serializer.validated_data["transaction_id"]
        is_successful = serializer.validated_data["success"]

        with transaction.atomic():
            try:
                # یافتن تراکنش معلق متعلق به کیف‌پول کاربر جاری با قفل سطر
                tx = Transaction.objects.select_for_update().get(
                    id=tx_id, wallet__user=request.user, type=Transaction.Type.DEPOSIT
                )
            except Transaction.DoesNotExist:
                return Response(
                    {"detail": "تراکنش یافت نشد."}, status=status.HTTP_404_NOT_FOUND
                )

            if tx.status != Transaction.Status.PENDING:
                return Response(
                    {"detail": "این تراکنش قبلاً تعیین تکلیف شده است."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            wallet = Wallet.objects.select_for_update().get(id=tx.wallet_id)

            if is_successful:
                tx.status = Transaction.Status.SUCCESS
                tx.description = "شارژ موفق کیف‌پول"
                tx.save()

                wallet.balance += tx.amount
                wallet.save()

                return Response(
                    {
                        "detail": "کیف‌پول با موفقیت شارژ شد.",
                        "new_balance": str(wallet.balance),
                        "transaction_id": tx.id,
                        "status": tx.status,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                tx.status = Transaction.Status.FAILED
                tx.description = "تراکنش ناموفق بانکی"
                tx.save()

                return Response(
                    {
                        "detail": "پرداخت ناموفق بود.",
                        "transaction_id": tx.id,
                        "status": tx.status,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )


class TransactionHistoryView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(wallet__user=user).order_by("-created_at")

        tx_type = self.request.query_params.get("type")
        if tx_type:
            queryset = queryset.filter(type=tx_type)

        tx_status = self.request.query_params.get("status")
        if tx_status:
            queryset = queryset.filter(status=tx_status)

        return queryset

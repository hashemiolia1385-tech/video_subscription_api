from django.urls import path
from .views import (
    WalletView,
    DepositRequestView,
    DepositVerifyView,
    TransactionHistoryView,
)

urlpatterns = [
    path("wallet/", WalletView.as_view(), name="wallet-detail"),
    path("deposit/request/", DepositRequestView.as_view(), name="deposit-request"),
    path("deposit/verify/", DepositVerifyView.as_view(), name="deposit-verify"),
    path("transactions/", TransactionHistoryView.as_view(), name="transaction-history"),
]

from rest_framework import serializers
from .models import Wallet, Transaction


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["id", "balance", "created_at", "updated_at"]
        read_only_fields = ["id", "balance", "created_at", "updated_at"]


class DepositRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1000)


class DepositVerifySerializer(serializers.Serializer):
    transaction_id = serializers.IntegerField()
    success = serializers.BooleanField(default=True)


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "amount",
            "type",
            "status",
            "description",
            "created_at",
        ]
        read_only_fields = fields

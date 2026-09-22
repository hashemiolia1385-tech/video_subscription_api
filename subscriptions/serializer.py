from django.utils import timezone
from rest_framework import serializers
from .models import SubscriptionPlan, Subscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ["id", "name", "price", "duration_days", "description"]


class PurchaseSubscriptionSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField(required=True)
    auto_renew = serializers.BooleanField(default=False)

    def validate_plan_id(self, value):
        if not SubscriptionPlan.objects.filter(id=value).exists():
            raise serializers.ValidationError("پلن انتخابی معتبر نمی‌باشد.")
        return value


class SubscriptionDetailSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "start_date",
            "end_date",
            "status",
            "auto_renew",
            "created_at",
            "updated_at",
        ]


class CurrentSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    days_left = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            "id",
            "plan",
            "start_date",
            "end_date",
            "status",
            "auto_renew",
            "days_left",
            "is_valid",
            "created_at",
        ]

    def get_days_left(self, obj):
        now = timezone.now()
        if obj.end_date > now and obj.status == Subscription.Status.ACTIVE:
            return max((obj.end_date - now).days, 0)
        return 0

    def get_is_valid(self, obj):
        return (
            obj.status == Subscription.Status.ACTIVE and obj.end_date > timezone.now()
        )

from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from payments.models import Wallet, Transaction
from .models import SubscriptionPlan, Subscription
from .serializer import (
    SubscriptionPlanSerializer,
    PurchaseSubscriptionSerializer,
    SubscriptionDetailSerializer,
    CurrentSubscriptionSerializer,
)
from .permissions import IsAdminOrReadOnly


class SubscriptionPlanViewSet(viewsets.ModelViewSet):
    queryset = SubscriptionPlan.objects.all().order_by("price")
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAdminOrReadOnly]


class PurchaseSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PurchaseSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_id = serializer.validated_data["plan_id"]
        auto_renew = serializer.validated_data["auto_renew"]
        plan = SubscriptionPlan.objects.get(id=plan_id)
        user = request.user

        with transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(user=user)

            if wallet.balance < plan.price:
                return Response(
                    {"detail": "موجودی کیف‌پول شما برای خرید این اشتراک کافی نیست."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            wallet.balance -= plan.price
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                amount=plan.price,
                type=Transaction.Type.PAYMENT,
                status=Transaction.Status.SUCCESS,
                description=f"خرید {plan.name}",
            )

            now = timezone.now()
            active_sub = (
                Subscription.objects.filter(
                    user=user, status=Subscription.Status.ACTIVE, end_date__gt=now
                )
                .order_by("-end_date")
                .first()
            )

            if active_sub:
                start_date = active_sub.start_date
                end_date = active_sub.end_date + timedelta(days=plan.duration_days)
                active_sub.plan = plan
                active_sub.end_date = end_date
                active_sub.auto_renew = auto_renew
                active_sub.save()
                sub = active_sub
            else:
                start_date = now
                end_date = now + timedelta(days=plan.duration_days)
                sub = Subscription.objects.create(
                    user=user,
                    plan=plan,
                    start_date=start_date,
                    end_date=end_date,
                    status=Subscription.Status.ACTIVE,
                    auto_renew=auto_renew,
                )

        output_serializer = SubscriptionDetailSerializer(sub)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class MySubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()

        active_sub = (
            Subscription.objects.filter(
                user=request.user,
                status=Subscription.Status.ACTIVE,
                end_date__gt=now,
            )
            .order_by("-end_date")
            .first()
        )

        if not active_sub:
            return Response(
                {
                    "detail": "شما در حال حاضر هیچ اشتراک فعالی ندارید.",
                    "has_active_subscription": False,
                },
                status=status.HTTP_200_OK,
            )

        serializer = CurrentSubscriptionSerializer(active_sub)
        data = serializer.data
        data["has_active_subscription"] = True
        return Response(data, status=status.HTTP_200_OK)


class SubscriptionHistoryView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SubscriptionDetailSerializer

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )


class CancelSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        now = timezone.now()

        active_sub = (
            Subscription.objects.filter(
                user=request.user, status=Subscription.Status.ACTIVE, end_date__gt=now
            )
            .order_by("-end_date")
            .first()
        )

        if not active_sub:
            return Response(
                {"detail": "شما در حال حاضر اشتراک فعالی برای لغو کردن ندارید."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_sub.status = Subscription.Status.CANCELLED
        active_sub.auto_renew = False
        active_sub.save()

        return Response(
            {
                "detail": "اشتراک شما با موفقیت لغو شد و دسترسی قطع گردید.",
                "status": active_sub.status,
                "auto_renew": active_sub.auto_renew,
            },
            status=status.HTTP_200_OK,
        )


class ToggleAutoRenewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        now = timezone.now()
        active_sub = (
            Subscription.objects.filter(
                user=request.user, status=Subscription.Status.ACTIVE, end_date__gt=now
            )
            .order_by("-end_date")
            .first()
        )

        if not active_sub:
            return Response(
                {"detail": "اشتراک فعالی برای تغییر وضعیت تمدید خودکار یافت نشد."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        active_sub.auto_renew = not active_sub.auto_renew
        active_sub.save()

        status_msg = "فعال" if active_sub.auto_renew else "غیرفعال"
        return Response(
            {
                "detail": f"تمدید خودکار اشتراک با موفقیت {status_msg} شد.",
                "auto_renew": active_sub.auto_renew,
            },
            status=status.HTTP_200_OK,
        )

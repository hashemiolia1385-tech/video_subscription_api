from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SubscriptionPlanViewSet,
    PurchaseSubscriptionView,
    MySubscriptionView,
    SubscriptionHistoryView,
    CancelSubscriptionView,
    ToggleAutoRenewView,
)

router = DefaultRouter()
router.register(r"plans", SubscriptionPlanViewSet, basename="subscription-plan")

urlpatterns = [
    path("my-subscription/", MySubscriptionView.as_view(), name="my-subscription"),
    path("history/", SubscriptionHistoryView.as_view(), name="subscription-history"),
    path(
        "purchase/",
        PurchaseSubscriptionView.as_view(),
        name="subscription-purchase",
    ),
    path("cancel/", CancelSubscriptionView.as_view(), name="subscription-cancel"),
    path(
        "toggle-auto-renew/",
        ToggleAutoRenewView.as_view(),
        name="subscription-toggle-auto-renew",
    ),
    path("", include(router.urls)),
]

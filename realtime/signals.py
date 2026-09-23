from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from .services import send_realtime_notification

from payments.models import Transaction, Wallet
from subscriptions.models import Subscription


@receiver(post_save, sender=Transaction)
def transaction_notification_handler(sender, instance, created, **kwargs):
    """
    نوتیفیکیشن تایید پرداخت و شارژ کیف پول
    """
    # استخراج کاربر از روی آبجکت یا از روی والت
    user = getattr(instance, "user", None)
    if not user and hasattr(instance, "wallet"):
        user = getattr(instance.wallet, "user", None)

    if not user:
        return

    # بررسی موفق بودن تراکنش
    status = str(getattr(instance, "status", "")).lower()
    is_successful = status in [
        "completed",
        "successful",
        "paid",
        "success",
        "done",
        "true",
    ]

    if is_successful:
        t_type = str(getattr(instance, "transaction_type", "")).lower()
        amount = getattr(instance, "amount", 0)

        if "wallet" in t_type or "deposit" in t_type or "charge" in t_type:
            send_realtime_notification(
                user=user,
                notification_type=Notification.NotificationType.WALLET_CHARGED,
                title="شارژ کیف پول با موفقیت انجام شد",
                message=f"کیف پول شما به مبلغ {amount} با موفقیت شارژ گردید.",
            )
        else:
            send_realtime_notification(
                user=user,
                notification_type=Notification.NotificationType.PAYMENT_CONFIRMED,
                title="پرداخت تایید شد",
                message=f"تراکنش شما به مبلغ {amount} با موفقیت تایید شد.",
            )


@receiver(post_save, sender=Subscription)
def subscription_notification_handler(sender, instance, created, **kwargs):
    """
    نوتیفیکیشن تایید دریافت، تمدید یا لغو اشتراک
    """
    user = getattr(instance, "user", None)
    if not user:
        return

    status = str(getattr(instance, "status", "")).lower()

    if created or status in ["active", "activated"]:
        send_realtime_notification(
            user=user,
            notification_type=Notification.NotificationType.SUBSCRIPTION_ACTIVATED,
            title="اشتراک با موفقیت فعال شد",
            message="اشتراک شما با موفقیت برای حساب کاربری فعال گردید.",
        )
    elif not created:
        if status in ["canceled", "cancelled"]:
            send_realtime_notification(
                user=user,
                notification_type=Notification.NotificationType.SUBSCRIPTION_CANCELED,
                title="لغو اشتراک",
                message="اشتراک شما طبق درخواست لغو شد.",
            )
        elif status in ["renewed", "extended"]:
            send_realtime_notification(
                user=user,
                notification_type=Notification.NotificationType.SUBSCRIPTION_RENEWED,
                title="تمدید خودکار اشتراک",
                message="اشتراک شما با موفقیت تمدید شد.",
            )

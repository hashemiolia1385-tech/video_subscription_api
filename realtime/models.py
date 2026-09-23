from django.db import models
from django.conf import settings
from videos.models import Video


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        PAYMENT_CONFIRMED = "payment_confirmed", "تایید پرداخت"
        SUBSCRIPTION_ACTIVATED = "subscription_activated", "تایید دریافت اشتراک"
        WALLET_CHARGED = "wallet_charged", "تایید شارژ کیف پول"
        SUBSCRIPTION_RENEWED = "subscription_renewed", "تمدید اشتراک"
        SUBSCRIPTION_CANCELED = "subscription_canceled", "لغو اشتراک"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="کاربر",
    )
    notification_type = models.CharField(
        max_length=32,
        choices=NotificationType.choices,
        verbose_name="نوع اعلان",
    )
    title = models.CharField(max_length=255, verbose_name="عنوان")
    message = models.TextField(verbose_name="متن پیام")
    is_read = models.BooleanField(default=False, verbose_name="خوانده شده")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "اعلان"
        verbose_name_plural = "اعلان‌ها"

    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()}"


class VideoComment(models.Model):
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="ویدیو",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="video_comments",
        verbose_name="کاربر",
    )
    text = models.TextField(verbose_name="متن نظر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ارسال")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "نظر ویدیو"
        verbose_name_plural = "نظرات ویدیو"

    def __str__(self):
        return f"{self.user.username} on {self.video.title}"

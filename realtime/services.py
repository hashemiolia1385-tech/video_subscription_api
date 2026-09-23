from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Notification


def send_realtime_notification(user, notification_type, title, message):
    """
    ۱. ذخیره نوتیفیکیشن در دیتابیس
    ۲. ارسال بلادرنگ از طریق WebSocket به کانال اختصاصی کاربر
    """
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
    )

    channel_layer = get_channel_layer()
    group_name = f"user_{user.id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "send_notification",
            "id": notification.id,
            "notification_type": notification.notification_type,
            "title": notification.title,
            "message": notification.message,
            "created_at": notification.created_at.isoformat(),
        },
    )

    return notification

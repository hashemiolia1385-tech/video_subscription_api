import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import VideoComment
from videos.models import Video


class VideoCommentConsumer(AsyncWebsocketConsumer):
    """
    مدیریت دریافت، ثبت و انتشار آنی نظرات برای یک ویدیوی مشخص
    """

    async def connect(self):
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.video_id = self.scope["url_route"]["kwargs"]["video_id"]
        self.room_group_name = f"video_comments_{self.video_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get("action")

        if action == "ping":
            await self.send(text_data=json.dumps({"event_type": "pong"}))
            return

        if action == "new_comment":
            text = data.get("text", "").strip()
            if not text:
                return

            # ذخیره در دیتابیس به صورت آسنکرون
            comment = await self.save_comment(self.video_id, self.user, text)
            if not comment:
                return

            # انتشار برای تمام کاربرانی که صفحه این فیلم را باز دارند
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_comment",
                    "comment_id": comment.id,
                    "user": self.user.username,
                    "text": comment.text,
                    "created_at": comment.created_at.isoformat(),
                },
            )

    async def broadcast_comment(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": "comment_received",
                    "comment_id": event["comment_id"],
                    "user": event["user"],
                    "text": event["text"],
                    "created_at": event["created_at"],
                }
            )
        )

    async def video_rating_updated(self, event):
        """
        ارسال میانگین امتیاز جدید و تعداد کل نظرات به تمام کلاینت‌های متصل به اتاق ویدیو
        """
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": "rating_updated",
                    "average_rating": event["average_rating"],
                    "total_reviews": event["total_reviews"],
                }
            )
        )

    async def video_view_updated(self, event):
        """
        ارسال تغییر تعداد کل تماشاها و کاربران فعال به صورت زنده
        """
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": "view_updated",
                    "total_views": event["total_views"],
                }
            )
        )

    @database_sync_to_async
    def save_comment(self, video_id, user, text):
        try:
            video = Video.objects.get(id=video_id)
            return VideoComment.objects.create(video=video, user=user, text=text)
        except Video.DoesNotExist:
            return None


class WatchPartyConsumer(AsyncWebsocketConsumer):
    """
    کانسومر اتاق گفتگوی زنده واچ‌پارتی
    """

    async def connect(self):
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.video_id = self.scope["url_route"]["kwargs"]["video_id"]
        self.room_group_name = f"watch_party_{self.video_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "system_message",
                "message": f"کاربر {self.user.username} به اتاق پیوست.",
                "user": self.user.username,
            },
        )

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            if self.user and self.user.is_authenticated:
                try:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            "type": "system_message",
                            "message": f"کاربر {self.user.username} از اتاق خارج شد.",
                            "user": self.user.username,
                        },
                    )
                except Exception:
                    pass

            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get("action")

        if action == "ping":
            await self.send(text_data=json.dumps({"event_type": "pong"}))
            return

        if action == "chat_message":
            message = data.get("message", "").strip()
            if not message:
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_broadcast",
                    "message": message,
                    "sender": self.user.username,
                    "timestamp": timezone.now().isoformat(),
                },
            )
        if action in ["play", "pause", "seek"]:
            current_time = data.get("current_time", 0)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "video_sync_broadcast",
                    "action": action,
                    "current_time": current_time,
                    "sender": self.user.username,
                },
            )

    async def video_sync_broadcast(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": "video_sync",
                    "action": event["action"],
                    "current_time": event["current_time"],
                    "sender": event["sender"],
                }
            )
        )

    async def chat_broadcast(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": "chat_message",
                    "message": event["message"],
                    "sender": event["sender"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    async def system_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": "system",
                    "message": event["message"],
                    "user": event["user"],
                }
            )
        )


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    کانال اختصاصی اعلان‌های بلادرنگ هر کاربر (نوتیفیکیشن‌های مالی و اشتراکی)
    """

    async def connect(self):
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # گروه اختصاصی برای هر کاربر بر اساس شناسه کاربری
        self.notification_group_name = f"user_{self.user.id}"

        await self.channel_layer.group_add(
            self.notification_group_name, self.channel_name
        )
        await self.accept()

        # ارسال تعداد اعلان‌های خوانده‌نشده بلافاصله پس از اتصال
        unread_count = await self.get_unread_count()
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": "unread_count",
                    "count": unread_count,
                }
            )
        )

    async def disconnect(self, close_code):
        if hasattr(self, "notification_group_name"):
            await self.channel_layer.group_discard(
                self.notification_group_name, self.channel_name
            )

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        action = data.get("action")

        if action == "ping":
            await self.send(text_data=json.dumps({"event_type": "pong"}))
            return

        # اکشن برای خوانده‌شدن یک یا تمام اعلان‌ها
        if action == "mark_as_read":
            notification_id = data.get("notification_id")
            await self.mark_notification_read(notification_id)
            unread_count = await self.get_unread_count()
            await self.send(
                text_data=json.dumps(
                    {
                        "event_type": "unread_count",
                        "count": unread_count,
                    }
                )
            )

    async def send_notification(self, event):
        """
        دریافت پیام از لایه Channels/Signals و تحویل آن به سوکت کاربر
        """
        await self.send(
            text_data=json.dumps(
                {
                    "event_type": "notification",
                    "id": event.get("id"),
                    "notification_type": event.get("notification_type"),
                    "title": event.get("title"),
                    "message": event.get("message"),
                    "created_at": event.get("created_at"),
                }
            )
        )

    @database_sync_to_async
    def get_unread_count(self):
        from .models import Notification

        return Notification.objects.filter(user=self.user, is_read=False).count()

    @database_sync_to_async
    def mark_notification_read(self, notification_id=None):
        from .models import Notification

        if notification_id:
            Notification.objects.filter(id=notification_id, user=self.user).update(
                is_read=True
            )
        else:
            Notification.objects.filter(user=self.user, is_read=False).update(
                is_read=True
            )

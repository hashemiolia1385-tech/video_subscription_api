import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async

from rest_framework.test import APITestCase
from rest_framework import status

from videos.models import Video
from realtime.models import Notification, VideoComment
from realtime.consumers import VideoCommentConsumer, NotificationConsumer
from realtime.services import send_realtime_notification

User = get_user_model()


class RealtimeModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_viewer",
            password="StrongPassword123!",
        )
        self.video = Video.objects.create(
            title="Inception",
            description="Dream architecture movie",
            genre="Sci-Fi",
            duration=8880,
            video_url="/media/videos/inception.mp4",
        )

    def test_create_notification_all_types(self):
        """بررسی ذخیره‌سازی ۵ نوع اعلان مجاز"""
        types = [
            Notification.NotificationType.PAYMENT_CONFIRMED,
            Notification.NotificationType.SUBSCRIPTION_ACTIVATED,
            Notification.NotificationType.WALLET_CHARGED,
            Notification.NotificationType.SUBSCRIPTION_RENEWED,
            Notification.NotificationType.SUBSCRIPTION_CANCELED,
        ]

        for n_type in types:
            notif = Notification.objects.create(
                user=self.user,
                notification_type=n_type,
                title=f"تست {n_type}",
                message="پیام تستی سیستم",
            )
            self.assertFalse(notif.is_read)
            self.assertEqual(notif.user, self.user)
            self.assertEqual(notif.notification_type, n_type)

        self.assertEqual(self.user.notifications.count(), 5)

    def test_create_video_comment(self):
        """بررسی ثبت و رابطه نظر با کاربر و ویدیو"""
        comment = VideoComment.objects.create(
            video=self.video,
            user=self.user,
            text="فیلم فوق‌العاده‌ای بود، مخصوصاً پایان داستان!",
        )
        self.assertEqual(comment.video.title, "Inception")
        self.assertEqual(comment.user.username, "test_viewer")
        self.assertIn("فیلم فوق‌العاده‌ای بود", comment.text)
        self.assertEqual(self.video.comments.count(), 1)

    def test_notification_ordering(self):
        """بررسی مرتب‌سازی پیام‌ها بر اساس زمان (جدیدترین در ابتدا)"""
        n1 = Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.WALLET_CHARGED,
            title="پیام اول",
            message="متن ۱",
        )
        n2 = Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.PAYMENT_CONFIRMED,
            title="پیام دوم",
            message="متن ۲",
        )

        notifications = list(Notification.objects.filter(user=self.user))
        self.assertEqual(notifications[0].id, n2.id)
        self.assertEqual(notifications[1].id, n1.id)


class VideoCommentConsumerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="commenter_ali",
            password="StrongPassword123!",
        )
        self.video = Video.objects.create(
            title="Interstellar",
            description="Space travel",
            genre="Sci-Fi",
            duration=10140,
        )

    async def test_unauthenticated_connection_rejected(self):
        """تست عدم دسترسی کاربر احراز هویت نشده به سوکت کامنت‌ها"""
        communicator = WebsocketCommunicator(
            VideoCommentConsumer.as_asgi(), f"/ws/comments/{self.video.id}/"
        )
        communicator.scope["url_route"] = {"kwargs": {"video_id": str(self.video.id)}}
        communicator.scope["user"] = None

        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4001)

    async def test_post_comment_and_broadcast(self):
        """تست ارسال کامنت، ذخیره در دیتابیس و برودکست پیام به کاربر"""
        communicator = WebsocketCommunicator(
            VideoCommentConsumer.as_asgi(), f"/ws/comments/{self.video.id}/"
        )
        communicator.scope["url_route"] = {"kwargs": {"video_id": str(self.video.id)}}
        communicator.scope["user"] = self.user

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to(
            {"action": "new_comment", "text": "این فیلم فوق‌العاده است!"}
        )

        response = await communicator.receive_json_from()
        self.assertEqual(response["event_type"], "comment_received")
        self.assertEqual(response["user"], "commenter_ali")
        self.assertEqual(response["text"], "این فیلم فوق‌العاده است!")

        comment_exists = await database_sync_to_async(
            lambda: VideoComment.objects.filter(
                video=self.video, user=self.user, text="این فیلم فوق‌العاده است!"
            ).exists()
        )()
        self.assertTrue(comment_exists)

        await communicator.disconnect()


class NotificationConsumerTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notif_user",
            password="StrongPassword123!",
        )
        self.n1 = Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.WALLET_CHARGED,
            title="شارژ کیف پول",
            message="موجودی ۵۰ هزار تومان افزایش یافت.",
        )
        self.n2 = Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.SUBSCRIPTION_ACTIVATED,
            title="اشتراک طلایی فعال شد",
            message="اشتراک یک‌ماهه فعال گردید.",
        )

    async def test_notification_connection_and_unread_count(self):
        """تست دریافت تعداد پیام‌های خوانده‌نشده در لحظه اتصال و اکشن خوانده شدن"""
        communicator = WebsocketCommunicator(
            NotificationConsumer.as_asgi(), "/ws/notifications/"
        )
        communicator.scope["user"] = self.user

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertEqual(response["event_type"], "unread_count")
        self.assertEqual(response["count"], 2)

        await communicator.send_json_to(
            {"action": "mark_as_read", "notification_id": self.n1.id}
        )

        updated_response = await communicator.receive_json_from()
        self.assertEqual(updated_response["event_type"], "unread_count")
        self.assertEqual(updated_response["count"], 1)

        await communicator.disconnect()


class RealtimeNotificationServiceTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="signal_tester",
            password="StrongPassword123!",
        )

    def test_send_realtime_notification_creates_db_record(self):
        """تست صحت عملکرد سرویس ارسال اعلان و ثبت در دیتابیس"""
        notif = send_realtime_notification(
            user=self.user,
            notification_type=Notification.NotificationType.SUBSCRIPTION_ACTIVATED,
            title="تست فعال‌سازی",
            message="اشتراک شما فعال شد.",
        )

        self.assertIsNotNone(notif.id)
        self.assertEqual(notif.user, self.user)
        self.assertEqual(
            notif.notification_type,
            Notification.NotificationType.SUBSCRIPTION_ACTIVATED,
        )
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)


class RealtimeAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="api_user",
            password="StrongPassword123!",
        )
        self.client.force_authenticate(user=self.user)
        self.video = Video.objects.create(
            title="The Matrix",
            description="Cyberpunk movie",
            genre="Action",
            duration=8160,
        )
        self.notif1 = Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.WALLET_CHARGED,
            title="شارژ والت",
            message="کیف پول شارژ شد.",
            is_read=False,
        )
        self.notif2 = Notification.objects.create(
            user=self.user,
            notification_type=Notification.NotificationType.PAYMENT_CONFIRMED,
            title="پرداخت تایید شد",
            message="رسید پرداخت",
            is_read=True,
        )
        self.comment = VideoComment.objects.create(
            video=self.video,
            user=self.user,
            text="بهترین فیلم علمی تخیلی!",
        )

    def test_list_notifications(self):
        """تست دریافت لیست اعلان‌ها و فیلتر خوانده نشده‌ها"""
        response = self.client.get("/api/realtime/notifications/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data.get("results")
            if isinstance(response.data, dict) and "results" in response.data
            else response.data
        )
        self.assertEqual(len(results), 2)

        response_unread = self.client.get("/api/realtime/notifications/?unread=true")
        results_unread = (
            response_unread.data.get("results")
            if isinstance(response_unread.data, dict)
            and "results" in response_unread.data
            else response_unread.data
        )
        self.assertEqual(len(results_unread), 1)
        self.assertEqual(results_unread[0]["id"], self.notif1.id)

    def test_mark_single_notification_read(self):
        """تست علامت‌گذاری یک نوتیفیکیشن به عنوان خوانده شده"""
        response = self.client.post(
            f"/api/realtime/notifications/{self.notif1.id}/read/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

    def test_mark_all_notifications_read(self):
        """تست علامت‌گذاری دسته‌جمعی تمام نوتیفیکیشن‌ها"""
        response = self.client.post("/api/realtime/notifications/read-all/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Notification.objects.filter(user=self.user, is_read=False).exists()
        )

    def test_list_video_comments(self):
        """تست واکشی تاریخچه نظرات ویدیو"""
        response = self.client.get(f"/api/realtime/comments/{self.video.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = (
            response.data.get("results")
            if isinstance(response.data, dict) and "results" in response.data
            else response.data
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "بهترین فیلم علمی تخیلی!")
        self.assertEqual(results[0]["username"], "api_user")

from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Video, WatchHistory, Review
from subscriptions.models import Subscription, SubscriptionPlan

User = get_user_model()


class VideoListAndDetailAPITest(APITestCase):
    def setUp(self):
        self.list_url = reverse("video-list")
        self.regular_user = User.objects.create_user(
            username="viewer_user", password="Password123!"
        )
        self.admin_user = User.objects.create_superuser(
            username="admin_video",
            password="Password123!",
            email="admin_video@example.com",
        )
        self.video_sci_fi = Video.objects.create(
            title="Inception SciFi",
            genre="Sci-Fi",
            duration=7200,
            video_url="https://example.com/inception.mp4",
        )
        self.video_drama = Video.objects.create(
            title="The Godfather Drama",
            genre="Drama",
            duration=9000,
            video_url="https://example.com/godfather.mp4",
        )

    def test_anonymous_user_can_list_videos(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_videos_by_genre(self):
        response = self.client.get(f"{self.list_url}?genre=Drama")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "The Godfather Drama")

    def test_search_videos_by_title(self):
        response = self.client.get(f"{self.list_url}?search=Inception")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["title"], "Inception SciFi")

    def test_regular_user_cannot_create_video(self):
        self.client.force_authenticate(user=self.regular_user)
        payload = {"title": "New Movie", "duration": 5000}
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_user_can_create_video(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "title": "Created By Admin",
            "genre": "Comedy",
            "duration": 5400,
            "video_url": "https://example.com/comedy.mp4",
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Video.objects.filter(title="Created By Admin").exists())


class VideoAccessPermissionAPITest(APITestCase):
    def setUp(self):
        self.user_without_sub = User.objects.create_user(
            username="no_sub_user", password="Password123!"
        )
        self.user_with_sub = User.objects.create_user(
            username="subscribed_user", password="Password123!"
        )
        self.plan = SubscriptionPlan.objects.create(
            name="پلن پریمیوم", price=99000.00, duration_days=30
        )
        now = timezone.now()
        Subscription.objects.create(
            user=self.user_with_sub,
            plan=self.plan,
            start_date=now,
            end_date=now + timedelta(days=20),
            status=Subscription.Status.ACTIVE,
        )

        self.free_video = Video.objects.create(
            title="Free Open Movie",
            video_url="https://example.com/free.mp4",
            duration=3000,
            required_plan=None,
        )
        self.premium_video = Video.objects.create(
            title="Premium Blockbuster",
            video_url="https://example.com/premium.mp4",
            duration=7200,
            required_plan=self.plan,
        )

    def test_anonymous_can_watch_free_video(self):
        detail_url = reverse("video-detail", kwargs={"pk": self.free_video.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["video_url"], self.free_video.video_url)
        self.assertTrue(response.data["can_watch"])

    def test_user_without_subscription_cannot_see_premium_video_url(self):
        self.client.force_authenticate(user=self.user_without_sub)
        detail_url = reverse("video-detail", kwargs={"pk": self.premium_video.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIsNone(response.data["video_url"])
        self.assertFalse(response.data["can_watch"])

    def test_user_without_subscription_forbidden_from_stream_action(self):
        self.client.force_authenticate(user=self.user_without_sub)
        stream_url = reverse("video-stream", kwargs={"pk": self.premium_video.pk})
        response = self.client.get(stream_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_subscribed_user_can_access_premium_video_url_and_stream(self):
        self.client.force_authenticate(user=self.user_with_sub)

        detail_url = reverse("video-detail", kwargs={"pk": self.premium_video.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["video_url"], self.premium_video.video_url)
        self.assertTrue(response.data["can_watch"])

        stream_url = reverse("video-stream", kwargs={"pk": self.premium_video.pk})
        stream_response = self.client.get(stream_url)
        self.assertEqual(stream_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            stream_response.data["stream_url"], self.premium_video.video_url
        )


class WatchHistoryAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="viewer_history", password="Password123!"
        )
        self.video = Video.objects.create(
            title="History Sample Movie",
            video_url="https://example.com/movie.mp4",
            duration=1000,
            required_plan=None,
        )
        self.progress_url = reverse("video-progress", kwargs={"pk": self.video.pk})
        self.history_url = reverse("watch-history")

    def test_update_progress_success(self):
        self.client.force_authenticate(user=self.user)
        payload = {"progress": 350}
        response = self.client.post(self.progress_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["progress"], 350)
        self.assertFalse(response.data["is_completed"])

        history_obj = WatchHistory.objects.get(user=self.user, video=self.video)
        self.assertEqual(history_obj.progress, 350)

    def test_auto_mark_completed_when_exceeding_threshold(self):
        self.client.force_authenticate(user=self.user)
        payload = {"progress": 950}
        response = self.client.post(self.progress_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_completed"])

    def test_watch_history_list(self):
        WatchHistory.objects.create(
            user=self.user, video=self.video, progress=500, is_completed=False
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.history_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["progress"], 500)


class VideoReviewAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="reviewer_user", password="Password123!"
        )
        self.other_user = User.objects.create_user(
            username="second_reviewer", password="Password123!"
        )
        self.video = Video.objects.create(
            title="Review Target Movie",
            video_url="https://example.com/target.mp4",
            duration=6000,
        )
        self.review_url = reverse("video-reviews", kwargs={"pk": self.video.pk})

    def test_unauthenticated_user_cannot_post_review(self):
        payload = {"rating": 8, "comment": "عالی بود"}
        response = self.client.post(self.review_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_can_submit_review(self):
        self.client.force_authenticate(user=self.user)
        payload = {"rating": 9, "comment": "شاهکار بود"}
        response = self.client.post(self.review_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["rating"], 9)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertTrue(
            Review.objects.filter(user=self.user, video=self.video).exists()
        )

    def test_re_posting_review_updates_existing_one(self):
        self.client.force_authenticate(user=self.user)
        Review.objects.create(
            user=self.user, video=self.video, rating=5, comment="متوسط"
        )

        payload = {"rating": 10, "comment": "نظرم عوض شد، عالیه"}
        response = self.client.post(self.review_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Review.objects.filter(user=self.user, video=self.video).count(), 1
        )
        review = Review.objects.get(user=self.user, video=self.video)
        self.assertEqual(review.rating, 10)
        self.assertEqual(review.comment, "نظرم عوض شد، عالیه")

    def test_average_rating_calculated_in_video_detail(self):
        Review.objects.create(user=self.user, video=self.video, rating=8)
        Review.objects.create(user=self.other_user, video=self.video, rating=10)

        detail_url = reverse("video-detail", kwargs={"pk": self.video.pk})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["average_rating"], 9.0)

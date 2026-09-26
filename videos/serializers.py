from django.utils import timezone
from django.db.models import Avg
from rest_framework import serializers
from .models import Video, CastCrew, Profile, VideoCredit, WatchHistory, Review
from subscriptions.serializer import SubscriptionPlanSerializer
from subscriptions.models import Subscription


class CastCrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CastCrew
        fields = ["id", "full_name", "birth_date"]


class VideoCreditSerializer(serializers.ModelSerializer):
    person = CastCrewSerializer(read_only=True)
    person_id = serializers.PrimaryKeyRelatedField(
        queryset=CastCrew.objects.all(), source="person", write_only=True
    )
    role_type_display = serializers.CharField(
        source="get_role_type_display", read_only=True
    )

    class Meta:
        model = VideoCredit
        fields = [
            "id",
            "person",
            "person_id",
            "role_type",
            "role_type_display",
            "character_name",
        ]


class VideoListSerializer(serializers.ModelSerializer):
    required_plan = SubscriptionPlanSerializer(read_only=True)
    is_free = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "thumbnail",
            "duration",
            "genre",
            "release_date",
            "required_plan",
            "is_free",
            "average_rating",
            "uploaded_at",
        ]

    def get_is_free(self, obj):
        return obj.required_plan is None

    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(avg_score=Avg("rating"))["avg_score"]
        return round(avg, 1) if avg else None


class VideoDetailSerializer(serializers.ModelSerializer):
    required_plan = SubscriptionPlanSerializer(read_only=True)
    credits = VideoCreditSerializer(many=True, read_only=True)
    is_free = serializers.SerializerMethodField()
    can_watch = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "id",
            "title",
            "description",
            "video_url",
            "thumbnail",
            "duration",
            "genre",
            "release_date",
            "required_plan",
            "is_free",
            "can_watch",
            "average_rating",
            "credits",
            "uploaded_at",
        ]

    def get_is_free(self, obj):
        return obj.required_plan is None

    def _check_user_access(self, obj):
        request = self.context.get("request")
        if obj.required_plan is None:
            return True
        if not request or not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True

        now = timezone.now()
        return Subscription.objects.filter(
            user=request.user, status=Subscription.Status.ACTIVE, end_date__gt=now
        ).exists()

    def get_can_watch(self, obj):
        return self._check_user_access(obj)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self._check_user_access(instance):
            data["video_url"] = None
        return data

    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(avg_score=Avg("rating"))["avg_score"]
        return round(avg, 1) if avg else 0.0

    def get_thumbnail(self, obj):
        if not obj.thumbnail:
            return None
        thumb_str = str(obj.thumbnail)
        # اصلاح مسیرهای ذخیره‌شده در static/img بدون اضافه شدن پیشوند /media/
        if "static/img/" in thumb_str:
            idx = thumb_str.find("/static/img/")
            if idx != -1:
                return thumb_str[idx:]
            return f"/static/img/{thumb_str.split('/')[-1]}"
        if thumb_str.startswith("http://") or thumb_str.startswith("https://"):
            return thumb_str
        request = self.context.get("request")
        if request and hasattr(obj.thumbnail, "url"):
            return request.build_absolute_uri(obj.thumbnail.url)
        return getattr(obj.thumbnail, "url", thumb_str)


class WatchProgressSerializer(serializers.Serializer):
    progress = serializers.IntegerField(min_value=0)


class WatchHistorySerializer(serializers.ModelSerializer):
    video = VideoListSerializer(read_only=True)

    class Meta:
        model = WatchHistory
        fields = [
            "id",
            "video",
            "progress",
            "is_completed",
            "last_watched_at",
        ]
        read_only_fields = fields


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "username",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "username",
            "created_at",
            "updated_at",
        ]

    def validate_rating(self, value):
        if not (1 <= value <= 10):
            raise serializers.ValidationError("امتیاز باید عددی بین ۱ تا ۱۰ باشد.")
        return value

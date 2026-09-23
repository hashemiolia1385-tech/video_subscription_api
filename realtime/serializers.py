from rest_framework import serializers
from .models import Notification, VideoComment


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "title",
            "message",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["id", "notification_type", "title", "message", "created_at"]


class VideoCommentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = VideoComment
        fields = ["id", "video", "username", "text", "created_at"]
        read_only_fields = ["id", "username", "created_at"]
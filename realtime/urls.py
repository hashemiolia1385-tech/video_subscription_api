from django.urls import path
from .views import (
    NotificationListView,
    MarkNotificationReadView,
    VideoCommentListView,
)

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notification-list"),
    path(
        "notifications/read-all/",
        MarkNotificationReadView.as_view(),
        name="notification-read-all",
    ),
    path(
        "notifications/<int:pk>/read/",
        MarkNotificationReadView.as_view(),
        name="notification-read",
    ),
    path(
        "comments/<int:video_id>/",
        VideoCommentListView.as_view(),
        name="video-comments-list",
    ),
]

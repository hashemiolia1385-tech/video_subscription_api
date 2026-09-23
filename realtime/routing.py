from django.urls import re_path, path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r"^ws/comments/(?P<video_id>\d+)/$", consumers.VideoCommentConsumer.as_asgi()
    ),
    re_path(r"^ws/watch/(?P<video_id>\d+)/$", consumers.WatchPartyConsumer.as_asgi()),
    path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
]

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"^ws/watch/(?P<video_id>\d+)/$", consumers.WatchPartyConsumer.as_asgi()),
]

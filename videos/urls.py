from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoViewSet, WatchHistoryView, video_player_view

router = DefaultRouter()
router.register(r"videos", VideoViewSet, basename="video")

urlpatterns = [
    path("player/<int:pk>/", video_player_view, name="video-player"),
    path("api/videos/history/", WatchHistoryView.as_view(), name="watch-history"),
    path("api/", include(router.urls)),
]

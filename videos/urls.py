from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    VideoViewSet,
    WatchHistoryView,
    video_player_view,
    movie_detail_view,
    person_detail_view,
    stream_video,
)

router = DefaultRouter()
router.register(r"videos", VideoViewSet, basename="video")

urlpatterns = [
    path("movie/<int:pk>/", movie_detail_view, name="movie-detail"),
    path("player/<int:pk>/", video_player_view, name="video-player"),
    path("api/videos/history/", WatchHistoryView.as_view(), name="watch-history"),
    path("person/<int:pk>/", person_detail_view, name="person-detail"),
    path("api/", include(router.urls)),
    path("stream/<int:pk>/", stream_video, name="stream-video"),
]

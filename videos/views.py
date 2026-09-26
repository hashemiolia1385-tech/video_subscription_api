from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, filters, status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Avg
from subscriptions.permissions import IsAdminOrReadOnly
from .models import Video, WatchHistory, Review
from .serializers import (
    VideoListSerializer,
    VideoDetailSerializer,
    WatchProgressSerializer,
    WatchHistorySerializer,
    ReviewSerializer,
)
from .permissions import CanWatchVideo


def video_player_view(request, pk):
    video = get_object_or_404(Video, pk=pk)
    return render(request, "player.html", {"video": video})


class VideoViewSet(viewsets.ModelViewSet):
    queryset = (
        Video.objects.all()
        .prefetch_related("credits__person")
        .select_related("required_plan")
        .order_by("-uploaded_at")
    )
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "description", "genre"]

    def get_serializer_class(self):
        if self.action == "list":
            return VideoListSerializer
        return VideoDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        genre = self.request.query_params.get("genre")
        if genre:
            queryset = queryset.filter(genre__icontains=genre)
        return queryset

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def top_rated(self, request):
        """
        دریافت تمامی فیلم‌های اولیه برای اسلایدر لندینگ پیج با نمره پیش‌فرض 0.0
        """
        from django.db.models import Avg
        from django.db.models.functions import Coalesce
        from django.db.models import Value, FloatField

        videos = Video.objects.annotate(
            avg_rating=Coalesce(
                Avg("reviews__rating"), Value(0.0), output_field=FloatField()
            )
        ).order_by("-uploaded_at")[:15]
        serializer = self.get_serializer(videos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], permission_classes=[CanWatchVideo])
    def stream(self, request, pk=None):
        """
        ارائه مستقیم لینک استریم با چک کردن دقیق پرمیشن CanWatchVideo
        """
        video = self.get_object()
        return Response(
            {
                "id": video.id,
                "title": video.title,
                "stream_url": video.video_url,
                "duration": video.duration,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanWatchVideo],
    )
    def progress(self, request, pk=None):
        video = self.get_object()
        serializer = WatchProgressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        progress_seconds = serializer.validated_data["progress"]
        is_completed = progress_seconds >= (video.duration * 0.9)

        watch_history, created = WatchHistory.objects.update_or_create(
            user=request.user,
            video=video,
            defaults={
                "progress": progress_seconds,
                "is_completed": is_completed,
            },
        )

        if created:
            channel_layer = get_channel_layer()
            total_views = WatchHistory.objects.filter(video=video).count()
            async_to_sync(channel_layer.group_send)(
                f"video_comments_{video.id}",
                {
                    "type": "video_view_updated",
                    "total_views": total_views,
                },
            )

        return Response(
            {
                "detail": "پیشرفت تماشا با موفقیت ثبت شد.",
                "progress": watch_history.progress,
                "is_completed": watch_history.is_completed,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get", "post"], permission_classes=[])
    def reviews(self, request, pk=None):
        video = self.get_object()

        if request.method == "GET":
            reviews = video.reviews.select_related("user").order_by("-created_at")
            serializer = ReviewSerializer(reviews, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == "POST":
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {"detail": "برای ثبت نظر ابتدا باید وارد حساب کاربری خود شوید."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            serializer = ReviewSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            rating = serializer.validated_data["rating"]
            comment = serializer.validated_data.get("comment", "")

            review, created = Review.objects.update_or_create(
                user=request.user,
                video=video,
                defaults={"rating": rating, "comment": comment},
            )

            avg_rating = video.reviews.aggregate(avg=Avg("rating"))["avg"] or 0.0
            total_reviews = video.reviews.count()

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"video_comments_{video.id}",
                {
                    "type": "video_rating_updated",
                    "average_rating": round(avg_rating, 1),
                    "total_reviews": total_reviews,
                },
            )

            res_serializer = ReviewSerializer(review)
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(res_serializer.data, status=status_code)


class WatchHistoryView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WatchHistorySerializer

    def get_queryset(self):
        return (
            WatchHistory.objects.filter(user=self.request.user)
            .select_related("video")
            .order_by("-last_watched_at")
        )

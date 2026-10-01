import os
import re
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
from .models import Video, WatchHistory, Review, CastCrew, VideoCredit
from .serializers import (
    VideoListSerializer,
    VideoDetailSerializer,
    WatchProgressSerializer,
    WatchHistorySerializer,
    ReviewSerializer,
)
from .permissions import CanWatchVideo
from datetime import date
from django.http import StreamingHttpResponse


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


def movie_detail_view(request, pk):
    video = get_object_or_404(Video, pk=pk)
    return render(request, "movie_detail.html", {"video": video})


def video_player_view(request, pk):
    video = get_object_or_404(Video, pk=pk)
    is_party = request.GET.get("party") == "true"
    template_name = "watchparty_player.html" if is_party else "player.html"
    return render(request, template_name, {"video": video, "is_party": is_party})


def person_detail_view(request, pk):
    person = get_object_or_404(CastCrew, pk=pk)
    profile = getattr(person, "profile", None)

    age = None
    if person.birth_date:
        today = date.today()
        born = person.birth_date
        age = (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )

    credits = VideoCredit.objects.filter(person=person).select_related("video")

    context = {
        "person": person,
        "profile": profile,
        "age": age,
        "credits": credits,
    }
    return render(request, "person_detail.html", context)


def stream_video(request, pk):
    video = get_object_or_404(Video, pk=pk)
    path = video.video_url.lstrip("/")
    if not os.path.exists(path):
        return StreamingHttpResponse(status=404)

    file_size = os.path.getsize(path)
    range_header = request.META.get("HTTP_RANGE", "").strip()
    range_match = re.match(r"bytes=(\d+)-(\d+)?", range_header)

    if range_match:
        first_byte = int(range_match.group(1))
        last_byte = int(range_match.group(2)) if range_match.group(2) else file_size - 1
        length = last_byte - first_byte + 1

        def file_iterator(file_path, offset, length, chunk_size=8192):
            with open(file_path, "rb") as f:
                f.seek(offset)
                remaining = length
                while remaining > 0:
                    read_bytes = min(chunk_size, remaining)
                    data = f.read(read_bytes)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        response = StreamingHttpResponse(
            file_iterator(path, first_byte, length),
            status=206,
            content_type="video/mp4",
        )
        response["Content-Range"] = f"bytes {first_byte}-{last_byte}/{file_size}"
        response["Accept-Ranges"] = "bytes"
        response["Content-Length"] = str(length)
        return response

    # در صورت عدم ارسال Range، فایل کامل به صورت بازه‌ای استریم می‌شود
    return StreamingHttpResponse(open(path, "rb"), content_type="video/mp4")

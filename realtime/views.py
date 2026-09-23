from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Notification, VideoComment
from .serializers import NotificationSerializer, VideoCommentSerializer


class NotificationListView(generics.ListAPIView):
    """
    دریافت لیست اعلان‌های کاربر جاری با قابلیت فیلتر بر اساس خوانده‌نشده‌ها
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Notification.objects.filter(user=self.request.user)
        unread_only = self.request.query_params.get("unread", None)
        if unread_only is not None and unread_only.lower() in ["true", "1"]:
            queryset = queryset.filter(is_read=False)
        return queryset


class MarkNotificationReadView(APIView):
    """
    علامت‌گذاری یک اعلان مشخص یا تمام اعلان‌ها به عنوان خوانده‌شده
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        if pk:
            notification = get_object_or_404(Notification, id=pk, user=request.user)
            notification.is_read = True
            notification.save(update_fields=["is_read"])
            return Response(
                {"detail": "اعلان به عنوان خوانده‌شده علامت‌گذاری شد."},
                status=status.HTTP_200_OK,
            )

        # اگر شناسه داده نشود، همه اعلان‌های کاربر خوانده می‌شوند
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True
        )
        return Response(
            {"detail": "تمام اعلان‌ها به عنوان خوانده‌شده علامت‌گذاری شدند."},
            status=status.HTTP_200_OK,
        )


class VideoCommentListView(generics.ListAPIView):
    """
    دریافت لیست تاریخچه نظرات یک ویدیو
    """

    serializer_class = VideoCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        video_id = self.kwargs.get("video_id")
        return VideoComment.objects.filter(video_id=video_id)

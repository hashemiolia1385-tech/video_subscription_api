from rest_framework.permissions import BasePermission
from django.utils import timezone
from subscriptions.models import Subscription


class CanWatchVideo(BasePermission):
    """
    بررسی دسترسی تماشای فیلم:
    - فیلم رایگان: دسترسی برای همه آزاد است.
    - فیلم نیازمند اشتراک: کاربر باید لاگین باشد و اشتراک ACTIVE و دارای اعتبار زمانی داشته باشد.
    """

    message = "برای تماشای این فیلم، نیاز به تهیه اشتراک فعال دارید."

    def has_object_permission(self, request, view, obj):
        if obj.required_plan is None:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_staff:
            return True

        now = timezone.now()
        has_active_sub = Subscription.objects.filter(
            user=request.user, status=Subscription.Status.ACTIVE, end_date__gt=now
        ).exists()

        return has_active_sub


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """
    خواندن برای همه، اما ویرایش/حذف فقط برای نویسنده نظر یا ادمین.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(
            request.user and (request.user == obj.user or request.user.is_staff)
        )

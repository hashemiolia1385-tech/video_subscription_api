from django.contrib import admin
from .models import Video, CastCrew, Profile, VideoCredit, Review, WatchHistory


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "genre", "required_plan", "uploaded_at")
    list_filter = ("genre", "required_plan")


@admin.register(CastCrew)
class CastCrewAdmin(admin.ModelAdmin):
    list_display = ("full_name", "birth_date")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("cast_crew", "nationality")


@admin.register(VideoCredit)
class VideoCreditAdmin(admin.ModelAdmin):
    list_display = ("video", "person", "role_type", "character_name")
    list_filter = ("role_type",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "video", "rating", "created_at")
    list_filter = ("rating",)


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "video", "progress", "is_completed", "last_watched_at")
    list_filter = ("is_completed",)
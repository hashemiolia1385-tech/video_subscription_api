from django.db import models
from django.conf import settings
from subscriptions.models import SubscriptionPlan


class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    thumbnail = models.ImageField(upload_to="thumbnails/", blank=True, null=True)
    duration = models.PositiveIntegerField(help_text="Duration in seconds", default=0)
    genre = models.CharField(max_length=100, blank=True)
    release_date = models.DateField(null=True, blank=True)
    required_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="videos",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class CastCrew(models.Model):
    full_name = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name_plural = "Cast & Crew"


class Profile(models.Model):
    cast_crew = models.OneToOneField(
        CastCrew,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    biography = models.TextField(blank=True)
    photo = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )
    nationality = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Profile({self.cast_crew})"


class VideoCredit(models.Model):
    class RoleType(models.TextChoices):
        ACTOR = "actor", "Actor"
        DIRECTOR = "director", "Director"
        WRITER = "writer", "Writer"
        CINEMATOGRAPHER = "cinematographer", "Cinematographer"
        OTHER = "other", "Other"

    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="credits")
    person = models.ForeignKey(
        CastCrew, on_delete=models.CASCADE, related_name="credits"
    )
    role_type = models.CharField(max_length=30, choices=RoleType.choices)
    character_name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.person} - {self.role_type} in {self.video}"


class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "video")

    def __str__(self):
        return f"Review({self.user} on {self.video})"


class WatchHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="watch_history",
    )
    video = models.ForeignKey(
        Video, on_delete=models.CASCADE, related_name="watch_history"
    )
    progress = models.PositiveIntegerField(
        default=0, help_text="Watched duration in seconds"
    )
    is_completed = models.BooleanField(default=False)
    last_watched_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} watched {self.video} ({self.progress}s)"

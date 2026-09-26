from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path("", TemplateView.as_view(template_name="landing.html"), name="home"),
    path(
        "movies/",
        TemplateView.as_view(template_name="movies.html"),
        name="vinora-movies",
    ),
    path(
        "register/",
        TemplateView.as_view(template_name="register.html"),
        name="vinora-register",
    ),
    path(
        "login/", TemplateView.as_view(template_name="login.html"), name="vinora-login"
    ),
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/subscriptions/", include("subscriptions.urls")),
    path("api/payments/", include("payments.urls")),
    path("api/realtime/", include("realtime.urls")),
    path("", include("videos.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
    )

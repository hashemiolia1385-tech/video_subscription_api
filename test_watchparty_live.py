import os
import signal
import sys
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.contrib.auth import get_user_model
from playwright.sync_api import sync_playwright
from rest_framework_simplejwt.tokens import RefreshToken
from videos.models import Video

User = get_user_model()

BASE_URL = "http://127.0.0.1:8000"
USER_NAMES = [f"test_user{i}" for i in range(1, 5)]
TEST_PASSWORD = "Password123!"


def cleanup_database():
    print("\n🧹 در حال پاکسازی اکانت‌های تستی از دیتابیس...")
    try:
        users = User.objects.filter(username__in=USER_NAMES)
        count = users.count()
        if count > 0:
            users.delete()
            print(f"✨ اکانت‌های تستی ({', '.join(USER_NAMES)}) حذف شدند.")
    except Exception as e:
        print(f"⚠️ خطا در پاکسازی: {e}")


def get_jwt_token_direct(username, password):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password(password)
    user.is_active = True
    user.save()

    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def main():
    def sig_handler(sig, frame):
        cleanup_database()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    # یافتن شناسه فیلم (در صورت نبودن، اولین فیلم را برمی‌دارد)
    video = (
        Video.objects.filter(title__icontains="Inception").first()
        or Video.objects.first()
    )
    if not video:
        print("❌ هیچ ویدیویی در دیتابیس برای ساخت چت‌روم پیدا نشد!")
        return

    video_id = video.id
    print(f"🎬 چت‌روم اختصاصی: {video.title} (ID: {video_id})")

    print("🚀 در حال ایجاد کاربران و صدور توکن‌ها...")
    tokens = {user: get_jwt_token_direct(user, TEST_PASSWORD) for user in USER_NAMES}
    print("✅ توکن‌ها صادر شدند.")

    try:
        with sync_playwright() as p:
            print("🌐 در حال راه‌اندازی ۴ پنجره کرومیوم...")

            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            party_url = f"{BASE_URL}/player/{video_id}/"
            pages = []

            # باز کردن و اتصال هر ۴ کاربر
            for username in USER_NAMES:
                context = browser.new_context(viewport={"width": 640, "height": 600})
                page = context.new_page()
                pages.append(page)

                page.goto(party_url)
                page.fill("#jwtTokenInput", tokens[username])
                page.click("#connectBtn")
                page.wait_for_selector(".status-dot.online", timeout=15000)
                print(f"🟢 کاربر {username} متصل شد.")

            # ارسال پیام تست توسط test_user1
            time.sleep(1)
            pages[0].fill(
                "#chatInput", "سلام به همگی! به چت روم واچ پارتی ۴ نفره خوش اومدید."
            )
            pages[0].click("#sendBtn")

            print("\n" + "=" * 65)
            print("🎉 چت روم واچ پارتی ۴ نفره آنلاین و کاملاً پایدار است:")
            print("- با اکانت‌ها پیام بفرستید و دریافت بلادرنگ را ببینید.")
            print("- با بستن تمام پنجره‌ها، اسکریپت اکانت‌ها را پاک می‌کند.")
            print("=" * 65 + "\n")

            while True:
                time.sleep(1)
                # بررسی اینکه آیا حداقل یک پنجره باز است یا خیر
                alive_pages = [p for p in pages if not p.is_closed()]
                if not alive_pages:
                    print("🛑 تمامی پنجره‌های چت بسته شدند.")
                    break

    except Exception as e:
        print(f"⚠️ خطای اجرا: {e}")
    finally:
        cleanup_database()


if __name__ == "__main__":
    main()

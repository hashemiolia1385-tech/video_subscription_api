import os
import sys
import time
import signal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from videos.models import Video
from playwright.sync_api import sync_playwright

User = get_user_model()

BASE_URL = "http://127.0.0.1:8000"
USER1_NAME = "test_alice"
USER2_NAME = "test_bob"
TEST_PASSWORD = "Password123!"


def cleanup_database():
    print("\n🧹 در حال پاکسازی اکانت‌های تستی از دیتابیس...")
    try:
        users = User.objects.filter(username__in=[USER1_NAME, USER2_NAME])
        count = users.count()
        if count > 0:
            users.delete()
            print(f"✨ اکانت‌های تستی ({USER1_NAME} و {USER2_NAME}) حذف شدند.")
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
    token1 = get_jwt_token_direct(USER1_NAME, TEST_PASSWORD)
    token2 = get_jwt_token_direct(USER2_NAME, TEST_PASSWORD)
    print("✅ توکن‌ها صادر شدند.")

    try:
        with sync_playwright() as p:
            print("🌐 در حال راه‌اندازی دو پنجره کرومیوم...")

            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            context1 = browser.new_context(viewport={"width": 750, "height": 760})
            context2 = browser.new_context(viewport={"width": 750, "height": 760})

            page1 = context1.new_page()
            page2 = context2.new_page()

            party_url = f"{BASE_URL}/player/{video_id}/"

            # اتصال Alice
            page1.goto(party_url)
            page1.fill("#jwtTokenInput", token1)
            page1.click("#connectBtn")
            page1.wait_for_selector(".status-dot.online", timeout=15000)
            print(f"🟢 کاربر {USER1_NAME} متصل شد.")

            # اتصال Bob
            page2.goto(party_url)
            page2.fill("#jwtTokenInput", token2)
            page2.click("#connectBtn")
            page2.wait_for_selector(".status-dot.online", timeout=15000)
            print(f"🟢 کاربر {USER2_NAME} متصل شد.")

            # ارسال پیام تست
            time.sleep(1)
            page1.fill("#chatInput", "سلام باب! به چت روم واچ پارتی خوش اومدی.")
            page1.click("#sendBtn")

            print("\n" + "=" * 65)
            print("🎉 چت روم واچ پارتی آنلاین و کاملاً پایدار است:")
            print("- با هر دو اکانت پیام بفرستید و دریافت بلادرنگ را ببینید.")
            print("- با بستن پنجره‌ها، اسکریپت اکانت‌ها را پاک می‌کند.")
            print("=" * 65 + "\n")

            while True:
                time.sleep(1)
                p1_alive = not page1.is_closed()
                p2_alive = not page2.is_closed()
                if not p1_alive and not p2_alive:
                    print("🛑 پنجره‌های چت بسته شدند.")
                    break

    except Exception as e:
        print(f"⚠️ خطای اجرا: {e}")
    finally:
        cleanup_database()


if __name__ == "__main__":
    main()

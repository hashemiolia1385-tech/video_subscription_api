import os
import signal
import sys
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from playwright.sync_api import sync_playwright
from rest_framework_simplejwt.tokens import RefreshToken
from videos.models import Video
from subscriptions.models import Subscription, SubscriptionPlan

User = get_user_model()

BASE_URL = "http://127.0.0.1:8000"
USER_NAMES = ["test_user1", "test_user2"]
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


def get_jwt_token_and_active_subscription(username, password):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password(password)
    user.is_active = True
    user.save()

    # ایجاد اشتراک فعال برای کاربر تستی جهت مجاز بودن به واچ‌پارتی
    plan = SubscriptionPlan.objects.first()
    if plan:
        Subscription.objects.update_or_create(
            user=user,
            defaults={
                "plan": plan,
                "start_date": timezone.now(),
                "end_date": timezone.now() + timedelta(days=30),
                "status": Subscription.Status.ACTIVE,
                "auto_renew": False,
            },
        )

    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


def main():
    def sig_handler(sig, frame):
        cleanup_database()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    video = Video.objects.filter(id=1).first() or Video.objects.first()
    if not video:
        print("❌ هیچ فیلمی در دیتابیس پیدا نشد!")
        return

    video_id = video.id
    print(f"🎬 اتاق واچ‌پارتی برای فیلم: {video.title} (ID: {video_id})")

    print("🚀 در حال ایجاد ۲ کاربر تستی با اشتراک فعال و صدور توکن‌ها...")
    tokens = {
        user: get_jwt_token_and_active_subscription(user, TEST_PASSWORD)
        for user in USER_NAMES
    }
    print("✅ توکن‌ها و اشتراک فعال ایجاد شدند.")

    test_room_code = "party777"

    try:
        with sync_playwright() as p:
            print("🌐 در حال راه‌اندازی ۲ پنجره مرورگر متصل به یک اتاق مشترک...")

            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            # هر دو کاربر با یک لینک اتاق باز می‌شوند
            party_url = (
                f"{BASE_URL}/player/{video_id}/?party=true&room={test_room_code}"
            )
            pages = []

            for username in USER_NAMES:
                context = browser.new_context(viewport={"width": 680, "height": 760})
                page = context.new_page()
                pages.append(page)

                page.goto(party_url)
                page.fill("#jwtTokenInput", tokens[username])
                page.click("#connectBtn")
                page.wait_for_selector(".status-badge.online", timeout=15000)
                print(f"🟢 کاربر {username} به اتاق {test_room_code} متصل شد.")

            time.sleep(1)
            pages[0].fill(
                "#chatInput", "سلام! لینک اتاق رو گرفتم و با موفقیت بهت وصل شدم."
            )
            pages[0].click("#sendBtn")

            print("\n" + "=" * 65)
            print("🎉 واچ‌پارتی پویا با لینک اتاق اختصاصی فعال است:")
            print("- لینک اتاق در بالای صفحه پلیر برای هر کاربر وجود دارد.")
            print("- با توقف، پخش یا جلو/عقب بردن، وضعیت هر دو پنجره هماهنگ می‌ماند.")
            print("=" * 65 + "\n")

            while True:
                time.sleep(1)
                alive_pages = [page for page in pages if not page.is_closed()]
                if not alive_pages:
                    print("🛑 تمامی پنجره‌ها بسته شدند.")
                    break

    except Exception as e:
        print(f"⚠️ خطای اجرا: {e}")
    finally:
        cleanup_database()


if __name__ == "__main__":
    main()

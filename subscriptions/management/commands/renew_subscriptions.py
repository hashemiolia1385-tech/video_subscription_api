from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from subscriptions.models import Subscription
from payments.models import Wallet, Transaction
from realtime.services import send_realtime_notification
from realtime.models import Notification


class Command(BaseCommand):
    help = "بررسی اشتراک‌های منقضی‌شده و اجرای تمدید خودکار بر اساس موجودی کیف‌پول"

    def handle(self, *args, **options):
        now = timezone.now()
        self.stdout.write(self.style.NOTICE(f"شروع پردازش اشتراک‌ها در تاریخ: {now}"))

        expired_subscriptions = Subscription.objects.filter(
            status=Subscription.Status.ACTIVE,
            end_date__lte=now,
        ).select_related("user", "plan")

        renewed_count = 0
        expired_count = 0

        for sub in expired_subscriptions:
            user = sub.user
            plan = sub.plan

            if sub.auto_renew:
                with transaction.atomic():
                    wallet = Wallet.objects.select_for_update().get(user=user)

                    if wallet.balance >= plan.price:

                        wallet.balance -= plan.price
                        wallet.save()

                        Transaction.objects.create(
                            wallet=wallet,
                            amount=plan.price,
                            type=Transaction.Type.PAYMENT,
                            status=Transaction.Status.SUCCESS,
                            description=f"تمدید خودکار اشتراک {plan.name}",
                        )

                        sub.start_date = now
                        sub.end_date = now + timedelta(days=plan.duration_days)
                        sub.status = Subscription.Status.ACTIVE
                        sub.save()

                        send_realtime_notification(
                            user=user,
                            notification_type=Notification.NotificationType.SUBSCRIPTION_RENEWED,
                            title="تمدید موفقیت‌آمیز اشتراک",
                            message=f"اشتراک شما برای پلن {plan.name} به صورت خودکار تمدید گردید.",
                        )

                        renewed_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"اشتراک کاربر {user.username} با موفقیت تمدید شد."
                            )
                        )
                        continue
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"موجودی ناکافی برای کاربر {user.username}. انتقال به وضعیت منقضی."
                            )
                        )

            sub.status = Subscription.Status.EXPIRED
            sub.auto_renew = False
            sub.save()
            expired_count += 1

            send_realtime_notification(
                user=user,
                notification_type=Notification.NotificationType.SUBSCRIPTION_CANCELED,
                title="انقضای اشتراک",
                message=f"مهلت اشتراک شما به پایان رسید. برای دسترسی به فیلم‌ها مجدداً اشتراک تهیه کنید.",
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"عملیات پایان یافت. تمدید شده: {renewed_count} | منقضی شده: {expired_count}"
            )
        )

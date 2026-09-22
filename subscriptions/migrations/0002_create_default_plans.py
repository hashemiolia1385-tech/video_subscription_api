from django.db import migrations


def create_default_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    plans = [
        {
            "name": "اشتراک ماهانه",
            "price": 99000.00,
            "duration_days": 30,
            "description": "دسترسی نامحدود 30 روزه به تمام محتوا ها.",
        },
        {
            "name": "اشتراک 6 ماهه",
            "price": 490000.00,
            "duration_days": 180,
            "description": "دسترسی نامحدود 6 ماهه با تخفیف ویژه",
        },
        {
            "name": "اشتراک 12 ماهه",
            "price": 890000.00,
            "duration_days": 365,
            "description": "به صرفه ترین اشتراک سالانه با دسترسی کامل",
        },
    ]

    for plan_data in plans:
        SubscriptionPlan.objects.get_or_create(
            name=plan_data["name"],
            defaults=plan_data,
        )


def remove_default_plans(apps, schema_editor):
    SubscriptionPlan = apps.get_model("subscriptions", "SubscriptionPlan")
    SubscriptionPlan.objects.filter(
        name__in=["اشتراک ماهانه", "اشتراک ۶ ماهه", "اشتراک ۱۲ ماهه"]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0001_initial"),
    ]
    operations = [
        migrations.RunPython(create_default_plans, remove_default_plans),
    ]

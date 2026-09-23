from django.core.management.base import BaseCommand
from videos.models import Video, CastCrew, VideoCredit
from subscriptions.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Seeds database with 10 real movies, credits and stream links"

    def handle(self, *args, **kwargs):
        self.stdout.write("در حال ایجاد اطلاعات اولیه فیلم‌ها...")

        monthly_plan = SubscriptionPlan.objects.filter(name__icontains="ماهانه").first()
        six_month_plan = SubscriptionPlan.objects.filter(
            name__icontains="۶ ماهه"
        ).first()

        movies_data = [
            {
                "title": "Inception (تلقین)",
                "description": "دام کاب یک دزد ماهر در استخراج اسرار ارزشمند از اعماق ضمیر ناخودآگاه در طول خواب است.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                "genre": "Sci-Fi / Action",
                "duration": 8880,
                "release_date": "2010-07-16",
                "required_plan": monthly_plan,
                "director": "Christopher Nolan",
                "actor": "Leonardo DiCaprio",
                "character": "Dom Cobb",
            },
            {
                "title": "Interstellar (میان‌ستاره‌ای)",
                "description": "تیمی از کاوشگران با استفاده از یک کرم‌چاله تازه کشف‌شده برای تضمین بقای بشریت به فضا سفر می‌کنند.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "genre": "Sci-Fi / Drama",
                "duration": 10140,
                "release_date": "2014-11-07",
                "required_plan": six_month_plan or monthly_plan,
                "director": "Christopher Nolan",
                "actor": "Matthew McConaughey",
                "character": "Cooper",
            },
            {
                "title": "The Dark Knight (شوالیه تاریکی)",
                "description": "بتمن با کمک ستوان جیم گوردون و هاروی دنت به مبارزه با تهدید جوکر می‌پردازد.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
                "genre": "Action / Crime",
                "duration": 9120,
                "release_date": "2008-07-18",
                "required_plan": monthly_plan,
                "director": "Christopher Nolan",
                "actor": "Christian Bale",
                "character": "Bruce Wayne / Batman",
            },
            {
                "title": "The Matrix (ماتریکس)",
                "description": "یک برنامه‌نویس کامپیوتر متوجه می‌شود که واقعیت اطراف او یک شبیه‌سازی سایبرنتیک است.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4",
                "genre": "Action / Sci-Fi",
                "duration": 8160,
                "release_date": "1999-03-31",
                "required_plan": None,
                "director": "Lana Wachowski",
                "actor": "Keanu Reeves",
                "character": "Neo",
            },
            {
                "title": "Pulp Fiction (داستان عامه‌پسند)",
                "description": "داستان‌های درهم‌تنیده از خلافکاران، دو آدم‌کش و یک بوکسور در لس‌آنجلس.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "genre": "Crime / Drama",
                "duration": 9240,
                "release_date": "1994-10-14",
                "required_plan": monthly_plan,
                "director": "Quentin Tarantino",
                "actor": "John Travolta",
                "character": "Vincent Vega",
            },
            {
                "title": "Fight Club (باشگاه مبارزه)",
                "description": "یک کارمند بی‌خواب با یک صابون‌ساز کاریزماتیک یک باشگاه مبارزه زیرزمینی تاسیس می‌کند.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                "genre": "Drama",
                "duration": 8340,
                "release_date": "1999-10-15",
                "required_plan": None,
                "director": "David Fincher",
                "actor": "Brad Pitt",
                "character": "Tyler Durden",
            },
            {
                "title": "Gladiator (گلادیاتور)",
                "description": "یک ژنرال رومی مورد خیانت قرار گرفته و برای انتقام از امپراتور به عنوان گلادیاتور بازمی‌گردد.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                "genre": "Action / Adventure",
                "duration": 9300,
                "release_date": "2000-05-05",
                "required_plan": monthly_plan,
                "director": "Ridley Scott",
                "actor": "Russell Crowe",
                "character": "Maximus",
            },
            {
                "title": "The Shawshank Redemption (رستگاری در شاوشنگ)",
                "description": "یک بانکدار به جرم قتلی که مرتکب نشده به حبس ابد محکوم شده و تلاش می‌کند امید خود را حفظ کند.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4",
                "genre": "Drama",
                "duration": 8520,
                "release_date": "1994-09-23",
                "required_plan": None,
                "director": "Frank Darabont",
                "actor": "Tim Robbins",
                "character": "Andy Dufresne",
            },
            {
                "title": "Whiplash (ویپلش)",
                "description": "یک درامر جوان و بااستعداد در یک هنرستان موسیقی زیر نظر استادی بی‌رحم آموزش می‌بیند.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
                "genre": "Drama / Music",
                "duration": 6420,
                "release_date": "2014-10-10",
                "required_plan": monthly_plan,
                "director": "Damien Chazelle",
                "actor": "Miles Teller",
                "character": "Andrew Neiman",
            },
            {
                "title": "Spider-Man: Into the Spider-Verse",
                "description": "مایلز مورالس قدرت‌های عنکبوتی پیدا می‌کند و با همتایان خود از ابعاد دیگر متحد می‌شود.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4",
                "genre": "Animation / Action",
                "duration": 7020,
                "release_date": "2018-12-14",
                "required_plan": monthly_plan,
                "director": "Peter Ramsey",
                "actor": "Shameik Moore",
                "character": "Miles Morales",
            },
        ]

        count = 0
        for item in movies_data:
            video, created = Video.objects.get_or_create(
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "video_url": item["video_url"],
                    "genre": item["genre"],
                    "duration": item["duration"],
                    "release_date": item["release_date"],
                    "required_plan": item["required_plan"],
                },
            )

            director, _ = CastCrew.objects.get_or_create(full_name=item["director"])
            VideoCredit.objects.get_or_create(
                video=video, person=director, role_type=VideoCredit.RoleType.DIRECTOR
            )

            actor, _ = CastCrew.objects.get_or_create(full_name=item["actor"])
            VideoCredit.objects.get_or_create(
                video=video,
                person=actor,
                role_type=VideoCredit.RoleType.ACTOR,
                character_name=item["character"],
            )
            count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"تعداد {count} فیلم با عوامل و استریم‌ها در دیتابیس ثبت شدند."
            )
        )

from django.core.management.base import BaseCommand
from videos.models import Video, CastCrew, VideoCredit, Profile
from subscriptions.models import SubscriptionPlan


class Command(BaseCommand):
    help = "Seeds database with 10 real movies, full descriptions, CastCrew, VideoCredit, and Artist Profiles"

    def handle(self, *args, **kwargs):
        self.stdout.write("در حال ایجاد و به‌روزرسانی اطلاعات اولیه فیلم‌ها و عوامل...")

        monthly_plan = SubscriptionPlan.objects.filter(name__icontains="ماهانه").first()
        six_month_plan = SubscriptionPlan.objects.filter(
            name__icontains="۶ ماهه"
        ).first()

        # اطلاعات جامع بیوگرافی و ملیت برای تک‌تک ۱۸ نفر از عوامل
        profiles_info = {
            "David Fincher": {
                "birth_date": "1962-08-28",
                "nationality": "آمریکایی",
                "photo": "/static/img/David_Fincher.jpg",
                "biography": "دیوید فینچر کارگردان سرشناس آمریکایی است که به خاطر دقت وسواس‌گونه در قاب‌بندی، فضاپردازی‌های روان‌شناختی تیره و آثاری ماندگار چون زودیاک، سون و شبکه اجتماعی شناخته می‌شود.",
            },
            "Brad Pitt": {
                "birth_date": "1963-12-18",
                "nationality": "آمریکایی",
                "photo": "/static/img/Brad_Pitt.jpeg",
                "biography": "برد پیت از برجسته‌ترین و جذاب‌ترین ستاره‌های هالیوود و برنده جوایز متعدد از جمله اسکار است که نقش‌های نمادینی همچون تایلر دردن و کلیف بوث را خلق کرده است.",
            },
            "Ridley Scott": {
                "birth_date": "1937-11-30",
                "nationality": "بریتانیایی",
                "photo": "/static/img/Ridley_Scott.jpeg",
                "biography": "ریدلی اسکات فیلمساز صاحب‌سبک بریتانیایی، استاد ساخت دنیاهای حماسی و تخیلی با عناوینی پیشگام نظیر بیگانه، بلید رانر و گلادیاتور در تاریخ سینما است.",
            },
            "Russell Crowe": {
                "birth_date": "1964-04-07",
                "nationality": "نیوزیلندی / استرالیایی",
                "photo": "/static/img/Russell_Crowe.jpeg",
                "biography": "راسل کرو بازیگر برنده جایزه اسکار است که با اجرای خیره‌کننده در نقش ماکسیموس در گلادیاتور و جان نش در ذهن زیبا جایگاه خود را میان بزرگان سینما ثبت کرد.",
            },
            "Quentin Tarantino": {
                "birth_date": "1963-03-27",
                "nationality": "آمریکایی",
                "photo": "/static/img/Quentin_Tarantino.jpeg",
                "biography": "کوئنتین تارانتینو نابغه روایت‌های غیرخطی، دیالوگ‌های پرکشش و ادای احترام به تاریخ سینماست که آثاری چون پالپ فیکشن و حرامزاده‌های لعنتی را خلق کرده است.",
            },
            "John Travolta": {
                "birth_date": "1954-02-18",
                "nationality": "آمریکایی",
                "photo": "/static/img/John_Travolta.jpeg",
                "biography": "جان تراولتا ستاره نام‌آشنای سینما است که در دهه هفتاد به اوج رسید و در دهه نود با بازی نبوغ‌آمیز در نقش وینسنت وگا در پالپ فیکشن رنسانسی هنری را رقم زد.",
            },
            "Peter Ramsey": {
                "birth_date": "1962-12-23",
                "nationality": "آمریکایی",
                "photo": "/static/img/Peter_Ramsey.jpeg",
                "biography": "پیتر رمزی تصویرساز و کارگردان نوآور آمریکایی است که با کارگردانی انیمیشن شگفت‌انگیز مرد عنکبوتی به جهان عنکبوتی موفق به دریافت جایزه اسکار شد.",
            },
            "Shameik Moore": {
                "birth_date": "1995-05-04",
                "nationality": "آمریکایی",
                "photo": "/static/img/Shameik_Moore.jpeg",
                "biography": "شمیک مور بازیگر، خواننده و صداپیشه پرانرژی است که صداپیشگی فراموش‌نشدنی مایلز مورالس در انیمیشن‌های دنیای عنکبوتی او را به شهرتی جهانی رساند.",
            },
            "Christopher Nolan": {
                "birth_date": "1970-07-30",
                "nationality": "بریتانیایی / آمریکایی",
                "photo": "/static/img/Christopher_Nolan.jpeg",
                "biography": "کریستوفر نولان پیشتاز سینمای مدرن در پرداختن به زمان، ماهیت حافظه و درام‌های پرتعلیق فکری با فیلم‌های تحسین‌شده‌ای چون اوپنهایمر، شوالیه تاریکی، تلقین و میان‌ستاره‌ای است.",
            },
            "Christian Bale": {
                "birth_date": "1974-01-30",
                "nationality": "بریتانیایی",
                "photo": "/static/img/Christian_Bale.jpeg",
                "biography": "کریستین بیل بازیگر متد و متعهد است که به خاطر تغییرات فیزیکی باورنکردنی و ایفای نقش جاودانه بروس وین در سه‌گانه شوالیه تاریکی شناخته می‌شود.",
            },
            "Lana Wachowski": {
                "birth_date": "1965-06-21",
                "nationality": "آمریکایی",
                "photo": "/static/img/Lana_Wachowski.jpeg",
                "biography": "لانا واچوفسکی نویسنده و فیلمساز جریان‌ساز آمریکایی است که همراه خواهرش با ساخت شاهکار ماتریکس انقلابی در جلوه‌های ویژه و فلسفه سایبرپانک در سینما پدید آورد.",
            },
            "Keanu Reeves": {
                "birth_date": "1964-09-02",
                "nationality": "کانادایی",
                "photo": "/static/img/Keanu_Reeves.jpeg",
                "biography": "کیانو ریوز ستاره محبوب و متواضع سینما است که در نقش‌های شمایلی نئو در سه‌گانه ماتریکس و جان ویک تاریخ‌سازی کرده است.",
            },
            "Frank Darabont": {
                "birth_date": "1959-01-28",
                "nationality": "آمریکایی / فرانسوی",
                "photo": "/static/img/Frank_Darabont.jpeg",
                "biography": "فرانک دارابونت کارگردان توانمند اقتباس‌های ادبی به ویژه داستان‌های استیون کینگ است که اثر جاودانه رستگاری در شاوشنگ و مسیر سبز را در کارنامه دارد.",
            },
            "Tim Robbins": {
                "birth_date": "1958-10-16",
                "nationality": "آمریکایی",
                "photo": "/static/img/Tim_Robbins.jpeg",
                "biography": "تیم رابینز بازیگر و کارگردان برنده اسکار است که با نقش‌آفرینی آرام، هوشمندانه و عمیق در قالب اندی دوفرین در فیلم رستگاری در شاوشنگ نقشی ماندگار خلق کرد.",
            },
            "Damien Chazelle": {
                "birth_date": "1985-01-19",
                "nationality": "آمریکایی",
                "photo": "/static/img/Damien_Chazelle.jpeg",
                "biography": "دیمین شزل جوان‌ترین برنده اسکار بهترین کارگردانی است که شور و هیجان ریتم موسیقی را با درام‌های روانی نظیر ویپلش و لالا لند به کمال رسانده است.",
            },
            "Miles Teller": {
                "birth_date": "1987-02-20",
                "nationality": "آمریکایی",
                "photo": "/static/img/Miles_Teller.jpeg",
                "biography": "مایلز تلر بازیگر نسل جدید هالیوود است که با اجرای انفجاری و فیزیکی در فیلم ویپلش و سپس تاپ گان ماوریک استعداد استثنایی خود را اثبات کرد.",
            },
            "Leonardo DiCaprio": {
                "birth_date": "1974-11-11",
                "nationality": "آمریکایی",
                "photo": "/static/img/Leonardo_DiCaprio.jpeg",
                "biography": "لئوناردو دی‌کاپریو از برترین بازیگران تاریخ معاصر سینما و برنده اسکار است که به انتخاب وسواس‌گونه فیلمنامه‌ها و همکاری با اسطوره‌های فیلمسازی شهرت دارد.",
            },
            "Matthew McConaughey": {
                "birth_date": "1969-11-04",
                "nationality": "آمریکایی",
                "photo": "/static/img/Matthew_McConaughey.jpeg",
                "biography": "متیو مک‌کانهی ستاره کاریزماتیک با برنده شدن اسکار برای باشگاه خریداران دالاس و نقش‌آفرینی فراموش‌نشدنی در سریال کارآگاه واقعی و فیلم میان‌ستاره‌ای قلب تماشاگران را تسخیر کرد.",
            },
        }

        movies_data = [
            {
                "title": "Fight Club (باشگاه مبارزه)",
                "description": "راوی ناشناس، یک کارمند اداری افسرده و مبتلا به بی‌خوابی مزمن است که از مصرف‌گرایی جامعه خسته شده است. او به طور اتفاقی با تایلر دردن، فروشنده‌ای کاریزماتیک و مرموز با دیدگاه‌های رادیکال آشنا می‌شود. آن دو با هم یک باشگاه مبارزه زیرزمینی تاسیس می‌کنند که به سرعت در سراسر کشور گسترش می‌یابد، اما این دوستی وارد بحران‌های روانی و امنیتی پیش‌بینی‌نشده‌ای می‌شود.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                "genre": "Drama",
                "duration": 8340,
                "release_date": "1999-10-15",
                "required_plan": None,
                "director": "David Fincher",
                "actor": "Brad Pitt",
                "character": "Tyler Durden",
                "cover": "/static/img/Fight_Club.jpg",
            },
            {
                "title": "Gladiator (گلادیاتور)",
                "description": "ماکسیموس مریدیوس، ژنرال برجسته و محبوب ارتش روم پس از پیروزی در نبردها، مورد حسادت کومودوس، فرزند امپراتور مارکوس آئورلیوس قرار می‌گیرد. کومودوس پس از قتل پدرش، دستور اعدام ماکسیموس و خانواده‌اش را صادر می‌کند. ماکسیموس فرار می‌کند اما به بردگی گرفته می‌شود و به عنوان گلادیاتور برای رسیدن به میدان نبرد کولوسئوم و انتقام خون خانواده‌اش می‌جنگد.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                "genre": "Action / Adventure",
                "duration": 9300,
                "release_date": "2000-05-05",
                "required_plan": monthly_plan,
                "director": "Ridley Scott",
                "actor": "Russell Crowe",
                "character": "Maximus",
                "cover": "/static/img/Gladiator.png",
            },
            {
                "title": "Pulp Fiction (داستان عامه‌پسند)",
                "description": "روایتی چندلایه، غیرخطی و کمدی‌سیاه از دنیای تبهکاران لس‌آنجلس؛ ماجراهای دو آدمکش حرفه‌ای به نام‌های وینسنت وگا و جولز وینفیلد، همسر جذاب یک رئیس مافیا به نام میا والاس، و یک بوکسور از نفس افتاده به نام بوچ کولیج در زنجیره‌ای از اتفاقات خشونت‌بار، طنزآمیز و تصادفی به یکدیگر گره می‌خورند.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "genre": "Crime / Drama",
                "duration": 9240,
                "release_date": "1994-10-14",
                "required_plan": monthly_plan,
                "director": "Quentin Tarantino",
                "actor": "John Travolta",
                "character": "Vincent Vega",
                "cover": "/static/img/Pulp_Fiction.jpg",
            },
            {
                "title": "Spider-Man: Into the Spider-Verse",
                "description": "مایلز مورالس، نوجوانی اهل بروکلین، پس از گزیده شدن توسط یک عنکبوت رادیواکتیو قدرت‌های فراانسانی کسب می‌کند. با باز شدن دریچه‌های ابعاد موازی جهان توسط کینگ‌پین، نسخه‌های متعددی از مردان و زنان عنکبوتی وارد دنیای او می‌شوند. مایلز باید بر تردیدهای خود غلبه کرده و با یادگیری معنای واقعی شجاعت، جلوی نابودی ساختار چندجهانی را بگیرد.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4",
                "genre": "Animation / Action",
                "duration": 7020,
                "release_date": "2018-12-14",
                "required_plan": monthly_plan,
                "director": "Peter Ramsey",
                "actor": "Shameik Moore",
                "character": "Miles Morales",
                "cover": "/static/img/Spider_Man_Into_the_Spider_Verse.png",
            },
            {
                "title": "The Dark Knight (شوالیه تاریکی)",
                "description": "بتمن با همراهی ستوان جیمز گوردون و دادستان شجاع هاروی دنت توانسته‌اند آرامش نسبی را به شهر گاتهام بازگردانند. اما با ظهور نابغه‌ای روانی و آنارشیست به نام جوکر که قوانین منطق و اخلاق را به تمسخر می‌گیرد، شهر به ورطه آشوب سقوط می‌کند و بتمن با آزمون‌هایی فرساینده در زمینه شرافت و فداکاری روبه‌رو می‌شود.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
                "genre": "Action / Crime",
                "duration": 9120,
                "release_date": "2008-07-18",
                "required_plan": monthly_plan,
                "director": "Christopher Nolan",
                "actor": "Christian Bale",
                "character": "Bruce Wayne / Batman",
                "cover": "/static/img/The_Dark_Knight.jpg",
            },
            {
                "title": "The Matrix (ماتریکس)",
                "description": "توماس اندرسون، یک کارشناس نرم‌افزار و هکری زیرزمینی با نام مستعار نئو، درمی‌یابد زندگی روزمره انسان‌ها در حقیقت یک توهم شبیه‌سازی‌شده به نام ماتریکس است که توسط هوش مصنوعی حاکم بر زمین ساخته شده است. او توسط مبارزانی سرکش به رهبری مورفیوس آزاد می‌شود تا نقش پیشگویی‌شده‌اش به عنوان منجی بشریت را تحقق بخشد.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4",
                "genre": "Action / Sci-Fi",
                "duration": 8160,
                "release_date": "1999-03-31",
                "required_plan": None,
                "director": "Lana Wachowski",
                "actor": "Keanu Reeves",
                "character": "Neo",
                "cover": "/static/img/The_Matrix.png",
            },
            {
                "title": "The Shawshank Redemption (رستگاری در شاوشنگ)",
                "description": "اندی دوفرین، بانکدار موفق و آرام، به اتهام واهی قتل همسرش به دو حبس ابد پیاپی در زندان مخوف شاوشنگ محکوم می‌شود. او در طول دو دهه اسارت، با پایبندی تزلزل‌ناپذیر به امید و شرافت انسانی، دوستی عمیقی با زندانی کهنه‌کاری به نام رد برقرار کرده و مسیر زندگی دیگر زندانیان را متحول می‌سازد.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4",
                "genre": "Drama",
                "duration": 8520,
                "release_date": "1994-09-23",
                "required_plan": None,
                "director": "Frank Darabont",
                "actor": "Tim Robbins",
                "character": "Andy Dufresne",
                "cover": "/static/img/The_Shawshank_Redemption.jpeg",
            },
            {
                "title": "Whiplash (ویپلش)",
                "description": "اندرو نیمن، نوازنده جوان ۱۹ ساله طبل و درامز، آرزوی بدل شدن به یکی از بزرگان موسیقی جاز را دارد. او وارد ارکستر معتبر کنسرواتوار شفرد به رهبری ترنس فلچر، استادی وسواسی، کمال‌گرا و بددهن می‌شود. روش‌های تدریس تحقیرآمیز و سخت‌گیرانه فلچر، اندرو را به مرز جنون، فرسودگی جسمی و تقابل اخلاقی می‌کشاند.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4",
                "genre": "Drama / Music",
                "duration": 6420,
                "release_date": "2014-10-10",
                "required_plan": monthly_plan,
                "director": "Damien Chazelle",
                "actor": "Miles Teller",
                "character": "Andrew Neiman",
                "cover": "/static/img/Whiplash.jpg",
            },
            {
                "title": "Inception (تلقین)",
                "description": "دام کاب، دزدی چیره‌دست در دنیای جاسوسی شرکتی است که هنر استخراج اسرار ناخودآگاه افراد در آسیب‌پذیرترین حالت رویا را دارد. به او فرصتی برای بازگشت نزد فرزندانش داده می‌شود، اما این بار مأموریت دزدی نیست؛ بلکه تلقین و کاشتن یک ایده در ذهن وارث یک امپراتوری تجاری در چند لایه عمیق رویا است.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                "genre": "Sci-Fi / Action",
                "duration": 8880,
                "release_date": "2010-07-16",
                "required_plan": monthly_plan,
                "director": "Christopher Nolan",
                "actor": "Leonardo DiCaprio",
                "character": "Dom Cobb",
                "cover": "/static/img/Inception.jpeg",
            },
            {
                "title": "Interstellar (میان‌ستاره‌ای)",
                "description": "در آینده‌ای رو به زوال که طوفان‌های گرد و غبار کشاورزی زمین را نابود کرده‌اند، کوپر، خلبان سابق ناسا و مهندس، مأموریت می‌یابد همراه با تیمی از دانشمندان از طریق کرم‌چاله‌ای در نزدیکی سیاره زحل به کهکشانی ناشناخته سفر کند تا سیاره‌ای مناسب برای سکونت و نجات نسل بشر بیابند.",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "genre": "Sci-Fi / Drama",
                "duration": 10140,
                "release_date": "2014-11-07",
                "required_plan": six_month_plan or monthly_plan,
                "director": "Christopher Nolan",
                "actor": "Matthew McConaughey",
                "character": "Cooper",
                "cover": "/static/img/Interstellar.jpeg",
            },
        ]

        count = 0
        for item in movies_data:
            video, _ = Video.objects.update_or_create(
                title=item["title"],
                defaults={
                    "description": item["description"],
                    "video_url": item["video_url"],
                    "genre": item["genre"],
                    "duration": item["duration"],
                    "release_date": item["release_date"],
                    "required_plan": item["required_plan"],
                    "thumbnail": item["cover"],
                },
            )

            # ۱. ثبت یا آپدیت کارگردان و پروفایل او
            dir_name = item["director"]
            dir_meta = profiles_info.get(dir_name, {})
            director, _ = CastCrew.objects.update_or_create(
                full_name=dir_name,
                defaults={"birth_date": dir_meta.get("birth_date")},
            )

            Profile.objects.update_or_create(
                cast_crew=director,
                defaults={
                    "biography": dir_meta.get("biography", ""),
                    "nationality": dir_meta.get("nationality", "بین‌المللی"),
                    "photo": dir_meta.get("photo", ""),
                },
            )

            VideoCredit.objects.get_or_create(
                video=video, person=director, role_type=VideoCredit.RoleType.DIRECTOR
            )

            # ۲. ثبت یا آپدیت بازیگر و پروفایل او
            act_name = item["actor"]
            act_meta = profiles_info.get(act_name, {})
            actor, _ = CastCrew.objects.update_or_create(
                full_name=act_name,
                defaults={"birth_date": act_meta.get("birth_date")},
            )

            Profile.objects.update_or_create(
                cast_crew=actor,
                defaults={
                    "biography": act_meta.get("biography", ""),
                    "nationality": act_meta.get("nationality", "بین‌المللی"),
                    "photo": act_meta.get("photo", ""),
                },
            )

            VideoCredit.objects.get_or_create(
                video=video,
                person=actor,
                role_type=VideoCredit.RoleType.ACTOR,
                character_name=item["character"],
            )
            count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"موفقیت‌آمیز: تعداد {count} فیلم همراه با کاور، استریم، عوامل، کردیت‌ها و ۱۸ پروفایل کامل هنرمندان در دیتابیس ذخیره شدند."
            )
        )

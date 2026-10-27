import json
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Post


class Command(BaseCommand):
    help = "Створює початкові дописи навчального блогу."

    def handle(self, *args, **options):
        author = get_user_model().objects.get(username="student")
        profile_path = Path(settings.BASE_DIR) / ".secrets" / "student-profile.json"
        default_body = (
            "Мене звати Максим. Я студент ДУІКТ, навчаюся за спеціальністю ІПЗ на п'ятому курсі, у магістратурі.\n\n"
            "Працюю системним адміністратором і займаюся підтримкою сайту. У цьому блозі зберігатиму "
            "нотатки з веброзробки та результати практичних робіт із Django.\n\n"
            "У вільний час граю у футбол. Цей блог — мій навчальний проєкт, у якому поєдную "
            "роботу з Python, базою даних та вебсторінками."
        )
        profile = json.loads(profile_path.read_text()) if profile_path.exists() else {}
        author.first_name = profile.get("name", "Максим")
        author.save(update_fields=["first_name"])
        now = timezone.now()
        entries = [
            ("Про мене", "pro-mene", profile.get("body", default_body), Post.Status.PUBLISHED, now),
            (
                "Чому я починаю з Django", "chomu-django",
                "Перший вебпроєкт простіше зрозуміти, коли його частини мають чіткі обов'язки. "
                "У Django модель описує дані, представлення отримує їх із бази, а шаблон формує сторінку. "
                "Така структура допомагає змінювати одну частину, не переписуючи весь застосунок.\n\n"
                "Для блогу достатньо кількох зрозумілих кроків: створити модель допису, застосувати міграції "
                "та підключити сторінки. Після цього можна додавати записи через готову адміністративну панель. "
                "Я починаю з невеликого набору можливостей, щоб перевірити кожну з них у браузері.\n\n"
                "Наступний корисний крок — розділити чернетки й опубліковані матеріали. Чернетка залишається "
                "доступною в адмінці, але не потрапляє до загального списку. Так можна спокійно готувати "
                "новий текст і відкрити його читачам лише після редагування.",
                Post.Status.PUBLISHED, now - timedelta(days=1),
            ),
            (
                "Що змінилося після першої міграції", "persha-mihratsiia",
                "Опис моделі у Python ще не створює таблицю в базі даних. Спочатку команда makemigrations "
                "записує заплановані зміни, а migrate застосовує їх. Після цього дописи можна зберігати "
                "та отримувати через ORM.\n\n"
                "У моделі блогу є заголовок, коротка мітка, текст, автор і дати. Статус визначає, "
                "чи готовий запис до публікації. Поле автора пов'язує допис із користувачем, "
                "тому один автор може мати декілька матеріалів.\n\n"
                "Міграції зберігаються окремими файлами. Якщо структуру потрібно змінити, я редагую модель, "
                "створюю нову міграцію та перевіряю результат. Наявні дані при цьому залишаються під контролем, "
                "а історія структури бази є частиною проєкту.\n\n"
                "Для цього навчального блогу використовую SQLite. Вона не потребує окремого сервера, "
                "тож можна зосередитися на моделях, запитах і відображенні записів.",
                Post.Status.PUBLISHED, now - timedelta(days=2),
            ),
            (
                "Нотатка, яку ще редагую", "pryvatna-chernetka",
                "Цей текст залишається чернеткою. Його можна редагувати в адміністративній панелі, "
                "але читачі не бачать його ні у списку, ні за прямою адресою.",
                Post.Status.DRAFT, now,
            ),
        ]
        for title, slug, body, status, publish in entries:
            Post.objects.update_or_create(
                slug=slug, author=author,
                defaults={"title": title, "body": body, "status": status, "publish": publish},
            )
        self.stdout.write(f"Дописи: {Post.objects.count()}; опубліковано: {Post.published.count()}; чернетки: {Post.objects.filter(status=Post.Status.DRAFT).count()}.")
        self.stdout.write(f"Перший допис: {Post.published.first().title}.")

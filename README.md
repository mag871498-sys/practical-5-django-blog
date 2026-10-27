# Практична робота №5. Розробка блогу

Django-блог за презентацією: модель Post, SQLite, статуси Draft/Published, адміністративна панель, ORM, список і повна сторінка допису.

## Запуск

Відкрити `start-blog.command` або виконати в папці проєкту:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/bootstrap.py
.venv/bin/python manage.py runserver 127.0.0.1:8005
```

Блог: <http://127.0.0.1:8005/>. Адмінка: <http://127.0.0.1:8005/admin/>.

Логін адміністратора `student`; випадковий пароль збережено локально у `.secrets/admin-login.json`. Цей файл і база даних виключені з Git. Команда bootstrap повторно не змінює пароль наявного адміністратора.

Перший допис «Про мене» містить відомості про автора Максима без прізвища й контактів. Його можна відредагувати в адмінці або створити `.secrets/student-profile.json` з полями `name` і `body` перед повторним запуском `seed_blog`.

## Перевірки

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py makemigrations --check --dry-run
.venv/bin/python manage.py test --verbosity 2
.venv/bin/python manage.py shell < scripts/orm_demo.py
```

Чернетка не відображається в блозі й повертає 404 за прямою адресою. Запити за роком використовують правильний lookup `publish__year`.

## Файли

- `blog/models.py`, `blog/admin.py`, `blog/views.py`, `blog/urls.py` — модель, адмінка та маршрути.
- `templates/blog/` і `static/css/blog.css` — шаблони та оформлення.
- `blog/migrations/0001_initial.py` — міграція таблиці дописів.
- `reports/output/pdf/Практична_робота_5_Розробка_блогу.pdf` — звіт.

## Здача

[GitHub](https://github.com/mag871498-sys/practical-5-django-blog) · [Історія комітів](https://github.com/mag871498-sys/practical-5-django-blog/commits/main/).

У звіті та `reports/evidence/` є скріншоти БД, сторінки блогу й адміністративної панелі.

Перегляд БД без зміни даних:

```bash
python3 scripts/inspect_database.py
open reports/tmp/database-viewer.html
```

Документація: [Django ORM](https://docs.djangoproject.com/en/5.2/topics/db/queries/), [менеджери](https://docs.djangoproject.com/en/5.2/topics/db/managers/), [адмінка](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/).

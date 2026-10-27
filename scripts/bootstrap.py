"""Prepare local secrets, SQLite, the administrator and initial blog posts."""

import json
import os
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
secret_dir = ROOT / ".secrets"
secret_dir.mkdir(exist_ok=True)
os.chmod(secret_dir, 0o700)
key = secret_dir / "django-key"
if not key.exists():
    key.write_text(secrets.token_urlsafe(64))
os.chmod(key, 0o600)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myblog.settings")

import django
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command

call_command("migrate", interactive=False)
user_model = get_user_model()
if not user_model.objects.filter(username="student").exists():
    password = secrets.token_urlsafe(24)
    os.environ["DJANGO_SUPERUSER_PASSWORD"] = password
    call_command("createsuperuser", username="student", email="", interactive=False)
    del os.environ["DJANGO_SUPERUSER_PASSWORD"]
    credentials = secret_dir / "admin-login.json"
    credentials.write_text(json.dumps({"username": "student", "password": password}, indent=2))
    os.chmod(credentials, 0o600)
call_command("seed_blog")
print("Дані для входу адміністратора: .secrets/admin-login.json")

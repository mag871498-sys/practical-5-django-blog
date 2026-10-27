from django.contrib.auth import get_user_model
from django.utils import timezone
from blog.models import Post


def show(expression):
    print(">>> " + expression)
    print(repr(eval(expression, globals())))


print("## Створення та оновлення")
User = get_user_model()
user = User.objects.get(username="student")
before = Post.objects.count()
print(">>> user = User.objects.get(username='student')")
print(">>> post = Post(title='Навчальний допис ORM', slug='orm-save-demo', body='Текст для ORM.', author=user)")
post = Post(title="Навчальний допис ORM", slug="orm-save-demo", body="Текст для ORM.", author=user)
print(">>> post.save()")
post.save()
show("post.title")
print(">>> extra = Post.objects.create(title='Навчальний допис create', slug='orm-create-demo', body='Ще один текст.', author=user)")
extra = Post.objects.create(title="Навчальний допис create", slug="orm-create-demo", body="Ще один текст.", author=user)
print(">>> post.title = 'Оновлений допис ORM'; post.save()")
post.title = "Оновлений допис ORM"
post.save()
show("Post.objects.get(pk=post.pk).title")
show("list(Post.objects.values_list('title', flat=True))")

print("## Запити та видалення")
year = timezone.localdate().year
show(f"list(Post.objects.filter(publish__year={year}).values_list('title', flat=True))")
show("list(Post.objects.exclude(title__startswith='Навчальний').values_list('title', flat=True))")
show("list(Post.objects.order_by('title').values_list('title', flat=True))")
show("list(Post.published.filter(title__startswith='Про').values_list('title', flat=True))")
show("Post.Status.choices")
show("Post.published.count()")
post_id, extra_id = post.pk, extra.pk
print(">>> post.delete(); extra.delete()")
post.delete()
extra.delete()
show("Post.objects.filter(pk__in=[post_id, extra_id]).exists()")
assert Post.objects.count() == before
print("PASS: ORM create, read, update, filter, exclude, order_by, published, delete.")

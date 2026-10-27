from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .models import Post


class BlogTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = get_user_model().objects.create_user(
            username="test_writer", password="test-only-password"
        )

    def create_post(self, title="A published post", **fields):
        values = {
            "title": title,
            "slug": slugify(title),
            "author": self.author,
            "body": "A short article about Django.",
            "status": Post.Status.PUBLISHED,
        }
        values.update(fields)
        return Post.objects.create(**values)


class PostModelTests(BlogTestCase):
    def test_new_post_is_a_draft_with_aware_timestamps(self):
        before = timezone.now()
        post = Post.objects.create(
            title="An unfinished idea", slug="unfinished", author=self.author,
            body="Still writing.",
        )
        after = timezone.now()

        self.assertEqual(post.status, Post.Status.DRAFT)
        for value in (post.publish, post.created, post.updated):
            self.assertTrue(timezone.is_aware(value))
            self.assertGreaterEqual(value, before)
            self.assertLessEqual(value, after)
        self.assertFalse(Post.published.filter(pk=post.pk).exists())

    def test_edit_updates_timestamp_but_preserves_creation_and_publish_dates(self):
        post = self.create_post()
        original_created = post.created
        original_publish = post.publish
        edited_at = post.updated + timedelta(minutes=5)

        with patch("django.db.models.fields.timezone.now", return_value=edited_at):
            post.body = "The revised article."
            post.save()
        post.refresh_from_db()

        self.assertEqual(post.updated, edited_at)
        self.assertEqual(post.created, original_created)
        self.assertEqual(post.publish, original_publish)

    def test_publishing_and_unpublishing_changes_public_manager_results(self):
        post = self.create_post(status=Post.Status.DRAFT)
        self.assertFalse(Post.published.filter(pk=post.pk).exists())

        post.status = Post.Status.PUBLISHED
        post.save()
        self.assertTrue(Post.published.filter(pk=post.pk).exists())

        post.status = Post.Status.DRAFT
        post.save()
        self.assertFalse(Post.published.filter(pk=post.pk).exists())
        self.assertTrue(Post.objects.filter(pk=post.pk).exists())

    def test_author_reverse_relation_and_cascade_deletion(self):
        first = self.create_post("First article")
        second = self.create_post("Second article")
        self.assertCountEqual(self.author.blog_posts.all(), [first, second])

        self.author.delete()
        self.assertFalse(Post.objects.filter(pk__in=[first.pk, second.pk]).exists())

    def test_absolute_url_opens_the_published_post(self):
        post = self.create_post()
        self.assertEqual(
            post.get_absolute_url(), reverse("blog:post_detail", kwargs={"id": post.pk})
        )
        response = self.client.get(post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["post"], post)


class PostViewTests(BlogTestCase):
    def test_list_shows_only_published_posts_newest_first(self):
        now = timezone.now()
        older = self.create_post("Older article", publish=now - timedelta(days=2))
        self.create_post("Private draft", status=Post.Status.DRAFT, publish=now)
        newer = self.create_post("Newer article", publish=now - timedelta(days=1))

        response = self.client.get(reverse("blog:post_list"))

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["posts"], [newer, older])
        self.assertNotContains(response, "Private draft")
        content = response.content.decode()
        self.assertLess(content.index("Newer article"), content.index("Older article"))

    def test_draft_detail_is_not_publicly_accessible(self):
        post = self.create_post("Private draft", status=Post.Status.DRAFT)
        response = self.client.get(post.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_missing_post_returns_404(self):
        response = self.client.get(reverse("blog:post_detail", kwargs={"id": 999999}))
        self.assertEqual(response.status_code, 404)

    def test_detail_displays_full_body_including_last_words(self):
        body = " ".join(f"detailword{number:02d}" for number in range(1, 41))
        post = self.create_post("Complete article", body=body)

        response = self.client.get(post.get_absolute_url())

        self.assertEqual(response.context["post"], post)
        self.assertContains(response, "Complete article")
        self.assertContains(response, body)
        self.assertContains(response, "detailword40")

    def test_list_limits_each_article_excerpt_to_thirty_words(self):
        body = " ".join(f"excerptword{number:02d}" for number in range(1, 36))
        post = self.create_post("Long article", body=body)

        response = self.client.get(reverse("blog:post_list"))

        self.assertContains(response, "excerptword30")
        self.assertNotContains(response, "excerptword31")
        self.assertNotContains(response, "excerptword35")
        self.assertContains(response, post.get_absolute_url())

    def test_post_content_is_escaped_in_list_and_detail(self):
        post = self.create_post(
            title="<script>alert('title')</script>",
            body='<script>alert("body")</script>',
        )
        for url in (reverse("blog:post_list"), post.get_absolute_url()):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, "<script>")
                self.assertContains(response, "&lt;script&gt;")


class PostAdminTests(BlogTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin_user = get_user_model().objects.create_superuser(
            username="test_admin", password="test-only-admin-password",
            email="admin@example.test",
        )

    def test_anonymous_visitor_is_redirected_to_admin_login(self):
        url = reverse("admin:blog_post_changelist")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('admin:login')}?next={url}")

    def test_regular_author_cannot_open_post_admin(self):
        self.client.force_login(self.author)
        url = reverse("admin:blog_post_changelist")
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('admin:login')}?next={url}")

    def test_admin_can_manage_both_drafts_and_published_posts(self):
        published = self.create_post("Public article")
        draft = self.create_post("Unfinished article", status=Post.Status.DRAFT)
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:blog_post_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["cl"].queryset, [published, draft])

    def test_admin_search_finds_title_and_body_matches(self):
        by_title = self.create_post("Searchneedle in title")
        by_body = self.create_post("Another article", body="A searchneedle in the body.")
        self.create_post("Unrelated article", body="Something entirely different.")
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse("admin:blog_post_changelist"), {"q": "searchneedle"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["cl"].queryset, [by_title, by_body])

    def test_admin_can_filter_posts_by_publication_status(self):
        self.create_post("Public article")
        draft = self.create_post("Unfinished article", status=Post.Status.DRAFT)
        self.client.force_login(self.admin_user)

        response = self.client.get(
            reverse("admin:blog_post_changelist"), {"status__exact": Post.Status.DRAFT}
        )

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["cl"].queryset, [draft])

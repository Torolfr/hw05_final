import shutil
import tempfile
from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post
from yatube.settings import POSTS_PER_PAGE

User = get_user_model()


class PostViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы 1',
            slug='test-slug',
            description='Это тестовая группа 1'
        )
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок группы 2',
            slug='test2-slug',
            description='Это тестовая группа 2'
        )
        cls.user = User.objects.create_user(username='Testuser')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.user)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('index'),
            'posts/group.html': reverse(
                'group_posts',
                args=[PostViewsTests.group.slug]
            ),
            'posts/new_post.html': reverse('new_post'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_group_profiles_pages_shows_correct_context(self):
        """Шаблон index, group, profile сформирован с правильным контекстом."""
        reverse_pages_names = (
            reverse('index'),
            reverse(
                'group_posts',
                args=[PostViewsTests.group.slug]
            ),
            reverse('profile', args=[PostViewsTests.user]),
        )
        for reverse_name in reverse_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page'][0]
                post_text_0 = first_object.text
                post_pub_date_0 = first_object.pub_date.replace(
                    microsecond=0,
                    tzinfo=None
                )
                post_author_0 = first_object.author
                post_group_0 = first_object.group
                self.assertEqual(post_text_0, PostViewsTests.post.text)
                self.assertEqual(
                    post_pub_date_0,
                    datetime.utcnow().replace(microsecond=0)
                )
                self.assertEqual(post_author_0, PostViewsTests.user)
                self.assertEqual(post_group_0, PostViewsTests.group)
                self.assertNotEqual(post_group_0, PostViewsTests.group2)

    def test_post_page_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        reverse_name = reverse(
            'post',
            kwargs={
                'username': PostViewsTests.user,
                'post_id': PostViewsTests.post.id
            }
        )
        response = self.authorized_client.get(reverse_name)
        first_object = response.context['post']
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date.replace(
            microsecond=0,
            tzinfo=None
        )
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(
            post_pub_date_0,
            datetime.utcnow().replace(microsecond=0)
        )
        self.assertEqual(post_author_0, PostViewsTests.user)
        self.assertEqual(post_group_0, PostViewsTests.group)

    def test_new_post_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        reverse_name = reverse(
            'post_edit',
            kwargs={
                'username': PostViewsTests.user,
                'post_id': PostViewsTests.post.id
            }
        )
        response = self.authorized_client.get(reverse_name)
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_cache_index(self):
        """Страница index закеширована"""
        self.authorized_client.get(reverse('index'))
        cache = make_template_fragment_key('index_page')
        self.assertNotEqual(cache, None)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Это тестовая группа'
        )
        cls.url_names = (
            reverse('index'),
            reverse('group_posts', kwargs={'slug': cls.group.slug}),
            reverse('profile', kwargs={'username': cls.user})
        )
        for i in range(15):
            Post.objects.create(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_paginator_first_page_contains_ten_records(self):
        """Количество записей на первой странице равно POSTS_PER_PAGE."""
        for reverse_name in PaginatorViewsTest.url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context.get('page').object_list),
                    POSTS_PER_PAGE
                )

    def test_paginator_second_page_contains_five_records(self):
        """Количество записей на второй странице равно (15 - POSTS_PER_PAGE).
        """
        for reverse_name in PaginatorViewsTest.url_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(
                    reverse_name + '?page=2'
                )
                self.assertEqual(
                    len(response.context.get('page').object_list),
                    15 - POSTS_PER_PAGE
                )


class PostViewsGifTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='Testuser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы 1',
            slug='test-slug',
            description='Это тестовая группа 1'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.test_image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=cls.test_image
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsGifTests.user)

    def test_index_group_profiles_pages_shows_correct_context_with_gif(self):
        """Шаблон index, group, profile сформирован с изображением."""
        reverse_pages_names = (
            reverse('index'),
            reverse(
                'group_posts',
                args=[PostViewsGifTests.group.slug]
            ),
            reverse('profile', args=[PostViewsGifTests.user]),
        )
        for reverse_name in reverse_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page'][0]
                post_text_0 = first_object.text
                post_pub_date_0 = first_object.pub_date.replace(
                    microsecond=0,
                    tzinfo=None
                )
                post_author_0 = first_object.author
                post_group_0 = first_object.group
                post_image_0 = first_object.image
                self.assertEqual(post_text_0, PostViewsGifTests.post.text)
                self.assertEqual(
                    post_pub_date_0,
                    datetime.utcnow().replace(microsecond=0)
                )
                self.assertEqual(post_author_0, PostViewsGifTests.post.author)
                self.assertEqual(post_group_0, PostViewsGifTests.post.group)
                self.assertEqual(post_image_0, PostViewsGifTests.post.image)


class PostViewsCommentsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Testuser')
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы 1',
            slug='test-slug',
            description='Это тестовая группа 1'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Первый комментарий'
        )

    def test_post_pages_shows_comments(self):
        """Шаблон post сформирован с комментариями."""
        reverse_name = reverse(
            'post',
            kwargs={
                'username': PostViewsCommentsTests.user,
                'post_id': PostViewsCommentsTests.post.id
            }
        )
        response = self.client.get(reverse_name)
        first_object = response.context['post']
        post_comments_0 = first_object.comments
        self.assertEqual(
            post_comments_0, PostViewsCommentsTests.post.comments
        )

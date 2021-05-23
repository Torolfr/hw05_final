import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post
from posts.forms import CommentForm, PostForm
from yatube.settings import POSTS_PER_PAGE

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(dir=settings.BASE_DIR))
class PostViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        self.authorized_client.force_login(PostViewsTests.user)
        cache.clear()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        username = PostViewsTests.user.username
        post_id = PostViewsTests.post.id
        slug = PostViewsTests.group.slug
        templates_pages_names = (
            ('posts/index.html', 'index', None),
            ('posts/group.html', 'group_posts', (slug,)),
            ('posts/new_post.html', 'new_post', None),
            ('posts/new_post.html', 'post_edit', (username, post_id)),
            ('posts/post.html', 'post', (username, post_id)),
            ('posts/profile.html', 'profile', (username,)),
            ('posts/follow.html', 'follow_index', None)
        )
        for template, url_name, args in templates_pages_names:
            with self.subTest(url_name=url_name):
                response = self.authorized_client.get(reverse(url_name,
                                                              args=args))
                self.assertTemplateUsed(response, template)

    def check_post_data(self, response, expected_data, is_post):
        """Вспомогательная функция для проверки атрибутов записи."""
        if is_post:
            self.assertIn('post', response.context)
            first_object = response.context['post']
        else:
            self.assertIn('page', response.context)
            first_object = response.context['page'][0]
        self.assertEqual(first_object.text, expected_data.text)
        self.assertEqual(
            first_object.pub_date, expected_data.pub_date
        )
        self.assertEqual(first_object.author, expected_data.author)
        self.assertEqual(first_object.group, expected_data.group)
        self.assertEqual(first_object.image, expected_data.image)

    def test_index_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        self.check_post_data(response, PostViewsTests.post, is_post=False)

    def test_group_posts_page_shows_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        slug = PostViewsTests.group.slug
        reverse_name = reverse('group_posts', args=(slug,))
        response = self.authorized_client.get(reverse_name)
        self.check_post_data(response, PostViewsTests.post, is_post=False)
        self.assertIn('group', response.context)
        group = response.context['group']
        self.assertEqual(group.title, PostViewsTests.group.title)
        self.assertEqual(group.slug, PostViewsTests.group.slug)
        self.assertEqual(group.description, PostViewsTests.group.description)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        reverse_name = reverse('profile', args=(PostViewsTests.user,))
        response = self.authorized_client.get(reverse_name)
        self.check_post_data(response, PostViewsTests.post, is_post=False)
        self.assertIn('author', response.context)
        self.assertEqual(PostViewsTests.user, response.context['author'])
        self.assertIn('following', response.context)

    def test_post_page_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        reverse_name = reverse('post', args=(PostViewsTests.user,
                                             PostViewsTests.post.id))
        response = self.authorized_client.get(reverse_name)
        self.check_post_data(response, PostViewsTests.post, is_post=True)
        self.assertIn('author', response.context)
        self.assertEqual(PostViewsTests.user, response.context['author'])
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], CommentForm)

    def test_new_post_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIn('is_edit', response.context)
        self.assertIs(False, response.context['is_edit'])

    def test_post_edit_page_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        reverse_name = reverse('post_edit', args=(PostViewsTests.user,
                                                  PostViewsTests.post.id))
        response = self.authorized_client.get(reverse_name)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIn('is_edit', response.context)
        self.assertIs(True, response.context['is_edit'])
        self.check_post_data(response, PostViewsTests.post, is_post=True)

    def test_cache_index(self):
        """Страница index закеширована"""
        response = self.authorized_client.get(reverse('index'))
        caсhe_page = response.content
        Post.objects.create(
            text='Новая запись',
            author=PostViewsTests.user,
        )
        response = self.authorized_client.get(reverse('index'))
        current_page = response.content
        self.assertEqual(caсhe_page, current_page)
        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        current_page = response.content
        self.assertNotEqual(current_page, caсhe_page)

    def test_profile_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей"""
        author = PostViewsTests.user
        username = author.username
        user2 = User.objects.create_user(username='Testuser2')
        self.reader_client = Client()
        self.reader_client.force_login(user2)
        count = Follow.objects.filter(author=author, user=user2).count()
        self.assertEqual(count, 0)
        self.reader_client.get(
            reverse('profile_follow', args=(username,))
        )
        count_follow = Follow.objects.filter(author=author, user=user2).count()
        self.assertEqual(count_follow, count + 1,)

    def test_profile_unfollow(self):
        """Авторизованный пользователь может удалять
        других пользователей из подписов"""
        author = PostViewsTests.user
        username = author.username
        user2 = User.objects.create_user(username='Testuser2')
        self.reader_client = Client()
        self.reader_client.force_login(user2)
        Follow.objects.create(
            user=user2,
            author=author
        )
        count = Follow.objects.filter(author=author, user=user2).count()
        self.assertEqual(count, 1)
        self.reader_client.get(
            reverse('profile_unfollow', args=(username,))
        )
        count_unfollow = Follow.objects.filter(
            author=author, user=user2).count()
        self.assertEqual(count_unfollow, count - 1)

    def test_follow_index(self):
        """Новая запись автора появляется в ленте подписчика
        и не появляется в ленте тех, кто не подписан на автора"""
        author = PostViewsTests.user
        user2 = User.objects.create_user(username='Testuser2')
        self.follow_client = Client()
        self.follow_client.force_login(user2)
        Follow.objects.create(
            user=user2,
            author=author
        )
        user3 = User.objects.create_user(username='Testuser3')
        self.unfollow_client = Client()
        self.unfollow_client.force_login(user3)
        form_data = {
            'text': 'Новая запись автора',
            'group': PostViewsTests.group.id,
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.first()
        follow_response = self.follow_client.get(reverse('follow_index'))
        first_object = follow_response.context['page'][0]
        self.assertEqual(first_object, new_post)
        unfollow_response = self.unfollow_client.get(reverse('follow_index'))
        self.assertEqual(
            len(unfollow_response.context.get('page').object_list), 0
        )


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
        objects = [
            Post(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group
            )
            for i in range(15)
        ]
        Post.objects.bulk_create(objects)

    def test_paginator_first_page_contains_ten_records(self):
        """Количество записей на первой странице равно POSTS_PER_PAGE."""
        response = self.client.get(reverse('index'))
        self.assertEqual(
            len(response.context.get('page').object_list), POSTS_PER_PAGE
        )

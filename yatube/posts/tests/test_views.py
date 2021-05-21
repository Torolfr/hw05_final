import shutil
import tempfile


from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
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
        for template, url_name, arg in templates_pages_names:
            with self.subTest(url_name=url_name):
                response = self.authorized_client.get(reverse(url_name,
                                                              args=arg))
                self.assertTemplateUsed(response, template)

    def check_post_data(self, first_object, expected_data):
        """Вспомогательная функция для проверки атрибутов записи."""
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
        self.assertIn('page', response.context)
        first_object = response.context['page'][0]
        self.check_post_data(first_object, PostViewsTests.post)

    def test_group_posts_page_shows_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        slug = PostViewsTests.group.slug
        reverse_name = reverse('group_posts', args=(slug,))
        response = self.authorized_client.get(reverse_name)
        self.assertIn('page', response.context)
        first_object = response.context['page'][0]
        self.check_post_data(first_object, PostViewsTests.post)
        self.assertIn('group', response.context)
        group = response.context['group']
        self.assertEqual(group.title, PostViewsTests.group.title)
        self.assertEqual(group.slug, PostViewsTests.group.slug)
        self.assertEqual(group.description, PostViewsTests.group.description)

    def test_profile_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        reverse_name = reverse('profile', args=(PostViewsTests.user,))
        response = self.authorized_client.get(reverse_name)
        self.assertIn('page', response.context)
        first_object = response.context['page'][0]
        self.check_post_data(first_object, PostViewsTests.post)
        self.assertIn('author', response.context)
        self.assertEqual(PostViewsTests.user, response.context['author'])
        self.assertIn('following', response.context)

    def test_post_page_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        reverse_name = reverse('post', args=(PostViewsTests.user,
                                             PostViewsTests.post.id))
        response = self.authorized_client.get(reverse_name)
        self.assertIn('post', response.context)
        first_object = response.context['post']
        self.check_post_data(first_object, PostViewsTests.post)
        self.assertIn('author', response.context)
        self.assertEqual(PostViewsTests.user, response.context['author'])
        self.assertIn('form', response.context)
        self.assertIn('CommentForm', repr(response.context['form']))
        self.assertIn('following', response.context)

    def test_new_post_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        self.assertIn('form', response.context)
        self.assertIn('PostForm', repr(response.context['form']))
        self.assertIn('is_edit', response.context)
        self.assertEqual(False, response.context['is_edit'])

    def test_post_edit_page_shows_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        reverse_name = reverse('post_edit', args=(PostViewsTests.user,
                                                  PostViewsTests.post.id))
        response = self.authorized_client.get(reverse_name)
        self.assertIn('form', response.context)
        self.assertIn('PostForm', repr(response.context['form']))
        self.assertIn('is_edit', response.context)
        self.assertEqual(True, response.context['is_edit'])
        self.assertIn('post', response.context)
        first_object = response.context['post']
        self.check_post_data(first_object, PostViewsTests.post)

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
            ('index', None),
            ('group_posts', (cls.group.slug,)),
            ('profile', (cls.user,))
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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_paginator_first_page_contains_ten_records(self):
        """Количество записей на первой странице равно POSTS_PER_PAGE."""
        for url_name, arg in PaginatorViewsTest.url_names:
            with self.subTest(url_name=url_name):
                response = self.authorized_client.get(reverse(url_name,
                                                              args=arg))
                self.assertEqual(
                    len(response.context.get('page').object_list),
                    POSTS_PER_PAGE
                )


class PostViewsCommentsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Это тестовая группа'
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
        username = PostViewsCommentsTests.user
        post_id = PostViewsCommentsTests.post.id
        reverse_name = reverse('post', args=(username, post_id))
        response = self.client.get(reverse_name)
        post = response.context['post']
        comment_0 = post.comments.first()
        self.assertEqual(comment_0.post, PostViewsCommentsTests.comment.post)
        self.assertEqual(comment_0.author,
                         PostViewsCommentsTests.comment.author)
        author = response.context['author']
        self.assertEqual(author, PostViewsCommentsTests.user)
        self.assertEqual(comment_0.text, PostViewsCommentsTests.comment.text)
        self.assertIn('form', response.context)
        self.assertIn('CommentForm', repr(response.context['form']))
        self.assertIn('following', response.context)

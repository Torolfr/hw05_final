from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.user = User.objects.create_user(username='Testuser')
        cls.user2 = User.objects.create_user(username='Testuser2')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.public_url_names = (
            reverse('index'),
            reverse('group_posts', args=[cls.group.slug]),
            reverse('profile', args=[cls.user]),
            reverse(
                'post',
                kwargs={
                    'username': cls.user,
                    'post_id': cls.post.id
                }
            ),
        )
        cls.reverse_post_edit_name = reverse(
            'post_edit',
            kwargs={
                'username': cls.user,
                'post_id': cls.post.id
            }
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user2)

    def test_public_url_exists_at_desired_location(self):
        """Общедоступные страницы доступны любому пользователю."""
        public_url_names = PostsURLTests.public_url_names
        for url in public_url_names:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_new_url_exists_at_desired_location(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_new_url_redirect_anonymous_on_auth_login(self):
        """Страница /new/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.client.get('/new/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/new/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group.html': PostsURLTests.public_url_names[1],
            'posts/new_post.html': '/new/',
            'posts/profile.html': PostsURLTests.public_url_names[2],
            'posts/post.html': PostsURLTests.public_url_names[3]
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_exists_at_desired_location(self):
        """Страница /post_id/edit/ доступна автору записи."""
        self.author_client = Client()
        self.author_client.force_login(PostsURLTests.user)
        response = self.author_client.get(PostsURLTests.reverse_post_edit_name)
        self.assertEqual(response.status_code, 200)

    def test_post_edit_url_redirect_anonymous_on_auth_login(self):
        """Страница /post_id/edit/ перенаправит анонимного
        пользователя на страницу /post_id/.
        """
        reverse_name1 = PostsURLTests.reverse_post_edit_name
        response = self.client.get(reverse_name1, follow=True)
        reverse_name2 = '/auth/login/?next=' + reverse_name1
        self.assertRedirects(response, reverse_name2)

    def test_post_edit_url_redirect_authorized_user_on_post_id(self):
        """Страница /post_id/edit/ перенаправит авторизованного
        пользователя (не автора записи) на страницу /post_id/.
        """
        reverse_name = PostsURLTests.reverse_post_edit_name
        response = self.authorized_client.get(reverse_name, follow=True)
        reverse_name = PostsURLTests.public_url_names[3]
        self.assertRedirects(response, reverse_name)

    def test_post_edit_url_use_correct_template(self):
        """Страница /post_id/edit/ использует соответствующий шаблон."""
        self.author_client = Client()
        self.author_client.force_login(PostsURLTests.user)
        reverse_name = PostsURLTests.reverse_post_edit_name
        response = self.author_client.get(reverse_name)
        self.assertTemplateUsed(response, 'posts/new_post.html')

    def test_incorrect_url_return_404_error(self):
        """Страница /abraabra/ возвращает 404 код ответа."""
        response = self.authorized_client.get('/abraabra/')
        self.assertEqual(response.status_code, 404)

    def test_comment_url_redirect_anonymous_on_auth_login(self):
        """Страница /post_id/comment/ перенаправит анонимного
        пользователя на страницу /auth/login/.
        """
        reverse_name1 = reverse(
            'add_comment',
            kwargs={
                'username': PostsURLTests.user,
                'post_id': PostsURLTests.post.id
            }
        )
        response = self.client.get(reverse_name1, follow=True)
        reverse_name2 = '/auth/login/?next=' + reverse_name1
        self.assertRedirects(response, reverse_name2)

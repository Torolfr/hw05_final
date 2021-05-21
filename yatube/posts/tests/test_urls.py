from http import HTTPStatus

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
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

    def test_post_url_exists_at_desired_location(self):
        """Проверка доступности адресов в posts.url."""
        username = PostsURLTests.user.username
        group_slug = PostsURLTests.group.slug
        post_id = PostsURLTests.post.id
        guest = self.client
        authorized = self.authorized_client
        permitted_url_names = (
            ('/', guest),
            (f'/group/{group_slug}/', guest),
            ('/new/', authorized),
            ('/follow/', authorized),
            (f'/{username}/{post_id}/', guest),
            (f'/{username}/{post_id}/edit/', authorized),
            (f'/{username}/', guest)
        )
        for url, client in permitted_url_names:
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_url_uses_correct_redirects(self):
        """Проверка redirect-ов для адресов posts.url."""
        user2 = User.objects.create_user(username='Testuser2')
        reader = Client()
        reader.force_login(user2)
        username = PostsURLTests.user.username
        post_id = PostsURLTests.post.id
        guest = self.client
        redirect_url_names = (
            ('/new/', guest,
             reverse('login') + '?next=' + reverse('new_post')),
            (f'/{username}/{post_id}/edit/', guest,
             reverse('login') + '?next=' + reverse('post_edit',
                                                   args=(username, post_id))),
            (f'/{username}/{post_id}/edit/', reader,
             reverse('post', args=(username, post_id))),
            (f'/{username}/follow/', guest,
             reverse('login') + '?next=' + reverse('profile_follow',
                                                   args=(username,))),
            (f'/{username}/follow/', reader,
             reverse('profile', args=(username,))),
            (f'/{username}/unfollow/', guest,
             reverse('login') + '?next=' + reverse('profile_unfollow',
                                                   args=(username,))),
            (f'/{username}/{post_id}/comment/', guest,
             reverse('login') + '?next=' + reverse('add_comment',
                                                   args=(username, post_id))),
        )
        for url, client, redirect in redirect_url_names:
            with self.subTest(url=url):
                response = client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_post_url_uses_correct_name_path(self):
        """Проверка name path() для адресов posts.url."""
        username = PostsURLTests.user.username
        group_slug = PostsURLTests.group.slug
        post_id = PostsURLTests.post.id
        url_names = (
            ('/', 'index', None),
            (f'/group/{group_slug}/', 'group_posts', (group_slug,)),
            ('/new/', 'new_post', None),
            ('/follow/', 'follow_index', None),
            (f'/{username}/{post_id}/', 'post', (username, post_id)),
            (f'/{username}/{post_id}/edit/', 'post_edit', (username, post_id)),
            (f'/{username}/{post_id}/comment/', 'add_comment',
             (username, post_id)),
            (f'/{username}/follow/', 'profile_follow', (username,)),
            (f'/{username}/unfollow/', 'profile_unfollow', (username,)),
            (f'/{username}/', 'profile', (username,))
        )
        for url, name, arg in url_names:
            with self.subTest(url=url):
                self.assertEqual(url, reverse(name, args=arg))

    def test_incorrect_url_return_404_error(self):
        """Страница /abraabra/abraabra/ возвращает 404 код ответа."""
        response = self.client.get('/abraabra/abraabra/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

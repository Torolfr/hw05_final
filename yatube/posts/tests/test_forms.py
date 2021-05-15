import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок группы 1',
            slug='test-slug',
            description='Это тестовая группа 1'
        )
        cls.user = User.objects.create_user(username='Testuser')
        cls.post = Post.objects.create(
            text='Первая запись',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_new_post(self):
        """Валидная форма создает новую запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Вторая запись',
            'group': PostFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group.id,
                text='Вторая запись',
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'text': 'Отредактированная первая запись',
            'group': PostFormTests.group.id,
        }
        reverse_names = (
            reverse(
                'post_edit',
                kwargs={
                    'username': PostFormTests.user,
                    'post_id': PostFormTests.post.id
                }
            ),
            reverse(
                'post',
                kwargs={
                    'username': PostFormTests.user,
                    'post_id': PostFormTests.post.id
                }
            )
        )
        response = self.authorized_client.post(
            reverse_names[0],
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse_names[1])
        self.assertTrue(
            Post.objects.filter(
                group=PostFormTests.group.id,
                text='Отредактированная первая запись',
            ).exists()
        )


class PostFormWithGifTests(TestCase):
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
        cls.post = Post.objects.create(
            text='Первая запись',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormWithGifTests.user)

    def test_create_post_with_picture(self):
        """Валидная форма создает запись в Post с изображением."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Вторая запись',
            'group': PostFormWithGifTests.group.id,
            'image': uploaded,
        }
        reverse_names = (
            reverse('new_post'),
            reverse('index'),
        )
        response = self.authorized_client.post(
            reverse_names[0],
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse_names[1])
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=PostFormWithGifTests.group.id,
                text='Вторая запись',
                image='posts/small.gif'
            ).exists()
        )


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test-slug',
            description='Это тестовая группа 1'
        )
        cls.user = User.objects.create_user(username='Testuser')
        cls.post = Post.objects.create(
            text='Первая запись',
            author=cls.user,
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Первый комментарий'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentFormTests.user)

    def test_add_comment_authorized_client(self):
        """Авторизованный клиент может создать новый комментарий в Comment."""
        comment_count = Comment.objects.count()
        form_data = {'text': 'Второй комментарий'}
        reverse_pages_names = (
            reverse(
                'add_comment',
                kwargs={
                    'username': CommentFormTests.user,
                    'post_id': CommentFormTests.post.id
                }
            ),
            reverse(
                'post',
                kwargs={
                    'username': CommentFormTests.user,
                    'post_id': CommentFormTests.post.id
                }
            )
        )
        response = self.authorized_client.post(
            reverse_pages_names[0],
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse_pages_names[1])
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(text='Второй комментарий').exists()
        )

    def test_add_comment_guest_client(self):
        """Анонимный клиент не  может создать новый комментарий в Comment."""
        comment_count = Comment.objects.count()
        form_data = {'text': 'Второй комментарий'}
        reverse_pages_names = (
            reverse(
                'add_comment',
                kwargs={
                    'username': CommentFormTests.user,
                    'post_id': CommentFormTests.post.id
                }
            ),
            reverse(
                'post',
                kwargs={
                    'username': CommentFormTests.user,
                    'post_id': CommentFormTests.post.id
                }
            )
        )
        response = self.guest_client.post(
            reverse_pages_names[0],
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            '/auth/login/?next=' + reverse_pages_names[0]
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertFalse(
            Comment.objects.filter(text='Второй комментарий').exists()
        )

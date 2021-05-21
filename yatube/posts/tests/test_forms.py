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
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(username='Testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Это тестовая группа'
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
        self.authorized_client.force_login(PostFormTests.user)

    def test_new_post_with_picture(self):
        """Валидная форма создает новую запись в Post с изображением."""
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
            'group': PostFormTests.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        new_post = Post.objects.first()
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.author, PostFormTests.user)
        self.assertEqual(new_post.group, PostFormTests.group)
        self.assertEqual(new_post.image, 'posts/small.gif')

    def test_new_post_guest_client(self):
        """Анонимный пользователь не  может создать новую запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Вторая запись',
            'group': PostFormTests.group.id,
        }
        response = self.client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('login') + '?next=' + reverse('new_post')
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post."""
        form_data = {
            'text': 'Отредактированная первая запись',
            'group': PostFormTests.group.id,
        }
        username = PostFormTests.user
        post_id = PostFormTests.post.id
        reverse_names = (
            reverse('post_edit', args=(username, post_id)),
            reverse('post', args=(username, post_id))
        )
        response = self.authorized_client.post(
            reverse_names[0],
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse_names[1])
        redacted_post = Post.objects.first()
        self.assertEqual(redacted_post.text, form_data['text'])
        self.assertEqual(redacted_post.author, PostFormTests.user)
        self.assertEqual(redacted_post.group, PostFormTests.group)

    def test_post_edit_reader_client(self):
        """Авторизованный пользователь не может редактировать чужую запись"""
        user = User.objects.create_user(username='Testuser2')
        reader_client = Client()
        reader_client.force_login(user)
        form_data = {
            'text': 'Отредактированная читателем запись',
            'group': PostFormTests.group.id,
        }
        username = PostFormTests.user
        post_id = PostFormTests.post.id
        reverse_names = (
            reverse('post_edit', args=(username, post_id)),
            reverse('post', args=(username, post_id))
        )
        response = reader_client.post(
            reverse_names[0],
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse_names[1])
        post = Post.objects.first()
        self.assertEqual(post.text, PostFormTests.post.text)
        self.assertEqual(post.author, PostFormTests.user)
        self.assertEqual(post.group, PostFormTests.group)


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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentFormTests.user)

    def test_add_comment_authorized_client(self):
        """Авторизованный пользователь может создать
        новый комментарий в Comment."""
        comment_count = Comment.objects.count()
        form_data = {'text': 'Новый комментарий'}
        username = CommentFormTests.user
        post_id = CommentFormTests.post.id
        reverse_names = (
            reverse('add_comment', args=(username, post_id)),
            reverse('post', args=(username, post_id))
        )
        response = self.authorized_client.post(
            reverse_names[0],
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertRedirects(response, reverse_names[1])
        new_comment = Comment.objects.first()
        self.assertEqual(new_comment.text, form_data['text'])
        self.assertEqual(new_comment.post, CommentFormTests.post)
        self.assertEqual(new_comment.author, username)

    def test_add_comment_guest_client(self):
        """Анонимный пользователь не  может создать
        новый комментарий в Comment."""
        comment_count = Comment.objects.count()
        form_data = {'text': 'Новый комментарий'}
        username = CommentFormTests.user
        post_id = CommentFormTests.post.id
        reverse_names = (
            reverse('add_comment', args=(username, post_id)),
            reverse('post', args=(username, post_id))
        )
        response = self.client.post(
            reverse_names[0],
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('login') + '?next=' + reverse_names[0]
        )
        self.assertEqual(Comment.objects.count(), comment_count)

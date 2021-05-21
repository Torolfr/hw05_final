from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Comment, Group, Post

User = get_user_model()


class ModelsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-group',
            description='Описание теcтовой группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий к тестовой записи'

        )

    def test_models_str(self):
        """Проверка метода __str__ моделей."""
        group = ModelsTest.group
        post = ModelsTest.post
        comment = ModelsTest.comment
        models = (
            (group, group.title),
            (post, post.text[:15]),
            (comment, comment.text[:15])
        )
        for model, expected_object_name in models:
            with self.subTest(model=model):
                self.assertEqual(expected_object_name, str(model))

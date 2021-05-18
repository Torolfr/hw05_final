from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class GroupModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название тестовой группы',
            slug='test-group',
            description='Описание теcтовой группы'
        )

    def test_group_str(self):
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_user = User.objects.create_user(username='Testuser')
        cls.post = Post.objects.create(
            text='Тестовый текст Тестовый текст',
            author=test_user,
        )

    def test_post_str(self):
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

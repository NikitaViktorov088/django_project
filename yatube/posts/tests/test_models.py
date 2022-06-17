from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='auth',
                                            email='test@email.ru',
                                            password='12345',),
            text='Тестовый пост'
        )
        cls.group = Group.objects.create(
            title=('Тестовая группа'),
            slug=('Тестовый слаг'),
            description=('Тестовое описание'),
        )

    def test_models_have_correct_object_names(self):
        """Проверям что у моделей правильно работает метод __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        expected_object_title = group.title
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))
        self.assertEqual(expected_object_title, str(group))

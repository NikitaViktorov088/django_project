from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Comment, Follow, Group, Post

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

        cls.comment = Comment.objects.create(
            author=User.objects.create_user(username='auth1'),
            text='Тестовый комментарий',
            post_id=cls.post.id
        )

    def test_models_have_correct_object_names(self):
        """Проверям что у моделей правильно работает метод __str__."""
        post = PostModelTest.post
        group = PostModelTest.group
        comment = PostModelTest.comment
        expected_object_title = group.title
        expected_object_name = post.text[:15]
        expected_object_name_1 = comment.text
        self.assertEqual(expected_object_name, str(post))
        self.assertEqual(expected_object_title, str(group))
        self.assertEqual(expected_object_name_1, str(comment))

    def test_verbose_name_post(self):
        post = PostModelTest.post
        fields_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for value, expected in fields_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_group(self):
        group = PostModelTest.group
        fields_verboses = {
            'title': 'Название группы',
            'slug': 'Название ссылки группы',
            'description': 'Описание группы',
        }
        for value, expected in fields_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    group._meta.get_field(value).verbose_name, expected)

    def test_verbose_name_comment(self):
        comment = PostModelTest.comment
        fields_verboses = {
            'post': 'Пост',
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Дата публикации',
        }
        for value, expected in fields_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    comment._meta.get_field(value).verbose_name, expected)


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follow = Follow.objects.create(
            user=User.objects.create_user(username='test_user'),
            author=User.objects.create_user(username='test_author')
        )

    def test_verbose_name_comment(self):
        follow = FollowModelTest.follow
        fields_verboses = {
            'user': 'Пользователь',
            'author': 'Автор',
        }
        for value, expected in fields_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    follow._meta.get_field(value).verbose_name, expected)

    def test_related_names(self):
        follow = FollowModelTest.follow
        fields_related_names = {
            'user': 'follower',
            'author': 'following',
        }
        for value, expected in fields_related_names.items():
            with self.subTest(value=value):
                self.assertEqual(
                    follow._meta.get_field(value).related_query_name(),
                    expected)

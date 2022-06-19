import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Comment, Group, Post, User


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug',
            description='Описание для тестовой группы'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post(self):
        """Создается новая запись в БД и происходит редирект на страницу"""
        """profile"""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.get(id=self.group.id)
        author = User.objects.get(username='test_user')
        group = Group.objects.get(title='Заголовок для тестовой группы')
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={
                                                   'username': 'test_user'}))
        self.assertEqual(post.text, 'Данные из формы')
        self.assertEqual(author.username, 'test_user')
        self.assertEqual(group.title, 'Заголовок для тестовой группы')
        self.assertEqual(Post.objects.first(), post)

    def test_guest_post_create(self):
        """Неавторизированный пользователь не может создавать посты"""
        form_data = {
            'text': 'Пост неавторизированного пользователя',
            'group': self.group.id
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(
            text='Пост неавторизированного пользователя').exists())

    def test_authorized_post_edit(self):
        """Авторизированный пользователь может редактировать посты"""
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.get(id=self.group.id)
        self.client.get(f'/posts/{post.id}/edit/')
        form_data = {
            'text': 'Измененный текст поста',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
        )
        post = Post.objects.get(id=self.group.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post.text, 'Измененный текст поста')

    def test_post_with_picture(self):
        """Создается новая запись в БД с картинкой и происходит редирект"""
        """на страницу profile"""
        count_posts = Post.objects.count()
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
            'text': 'Пост с картинкой',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.get(id=self.group.id)
        author = User.objects.get(username='test_user')
        group = Group.objects.get(title='Заголовок для тестовой группы')
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={
                                                   'username': 'test_user'}))
        self.assertEqual(post.text, 'Пост с картинкой')
        self.assertEqual(author.username, 'test_user')
        self.assertEqual(group.title, 'Заголовок для тестовой группы')

    def test_post_with_trash(self):
        temp_file = tempfile.TemporaryFile()
        err = 'Отправленный файл пуст.'
        response = self.authorized_client.post(
            reverse('posts:post_create'), {'image': temp_file})
        self.assertFormError(response, 'form', 'image', err)


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='test_author')
        cls.post_author = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост автора'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)

    def test_add_comment(self):
        count_comments = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        response = self.authorized_author.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post_author.id}),
            data=form_data,
            follow=True
        )
        comment = Comment.objects.get()
        self.assertEqual(Comment.objects.count(), count_comments + 1)
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={
                                                'post_id':
                                                self.post_author.id}))
        self.assertEqual(comment.text, 'Тестовый комментарий')

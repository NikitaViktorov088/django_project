from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='test_author')
        cls.user = User.objects.create_user(username='test_user')
        cls.post_author = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост автора',
            id='101')
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug',
        )

    def setUp(self):

        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)
        self.authorized_client.force_login(self.user)

    def test_public_page(self):
        """Общедоступные страницы достпны всем"""
        url_names = (
            '/',
            '/group/test_slug/',
            '/profile/test_author/',
            '/posts/101/'
        )
        for adress in url_names:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_url(self):
        """недоступны неавторизированному пользователю"""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_for_authorized_page(self):
        """Страница create/ доступна для авторизированного пользователя"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_athorized_client_for_edit(self):
        """Страница posts/101/edit для авторизированного пользователя"""
        """не владеющим этим постом"""
        response = self.authorized_client.get('/posts/101/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_author_edit_post(self):
        """Страница создания и редактирования поста доступна автору"""
        url_names = (
            '/posts/101/edit/',
            '/create/',
        )
        for adress in url_names:
            with self.subTest(adress=adress):
                response = self.authorized_author.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL использует соответствующий шаблон"""
        template_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/test_author/': 'posts/profile.html',
            '/posts/101/': 'posts/post_detail.html',
            '/posts/101/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in template_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_redirect_guest_client_on_login(self):
        """Страницы создания и редактирования поста не авторизированного"""
        """пользователя перенаправит на страницу логина"""
        template_url_names = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/101/edit/': '/auth/login/?next=/posts/101/edit/',
        }
        for url, template in template_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, template)

    def test_redirect_authorized_client_on_detail(self):
        """Страница реадктирования поста будет перенаправлять на страницу"""
        """детальной информации о посте"""
        response = self.authorized_client.get('/posts/101/edit/', follow=True)
        self.assertRedirects(response, '/posts/101/')

import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()


class PostTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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

        cls.user = User.objects.create_user(username='test_user')

        cls.user_author_1 = User.objects.create_user(username='test_author_1')

        cls.post_author_1 = Post.objects.create(
            author=cls.user_author_1,
            text='Тестовый пост автора 1',
            id='101',
            group=Group.objects.create(
                title='Заголовок для тестовой группы 1',
                slug='test_slug_1'))

        cls.user_author_2 = User.objects.create_user(username='test_author_2')

        cls.post_2 = Post.objects.create(
            author=cls.user_author_2,
            text='Тестовый пост автора 2',
            id='102',
            image=uploaded,
            group=Group.objects.create(
                title='Заголовок для тестовой группы 2',
                slug='test_slug_2'))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_author_1 = Client()
        self.authorized_author_2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author_1.force_login(self.user_author_1)
        self.authorized_author_2.force_login(self.user_author_2)

    def test_pages_uses_correct_template(self):
        """URL использует соответствующий шаблон"""
        template_page_names = {
            reverse('posts:index_list'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug_1'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={
                        'username': 'test_author_1'
                    }): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '101'}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': '101'}): 'posts/create_post.html',
        }
        for reverse_name, template in template_page_names.items():
            with self.subTest(template):
                response = self.authorized_author_1.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_pages_show_correct_context(self):
        """"Шаблон index получает правильный context"""
        response = self.authorized_client.get(reverse('posts:index_list'))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author.username
        post_group = first_object.group.title
        post_image = Post.objects.first().image
        self.assertEqual(post_text, 'Тестовый пост автора 2')
        self.assertEqual(post_author, 'test_author_2')
        self.assertEqual(post_group, 'Заголовок для тестовой группы 2')
        self.assertEqual(post_image, 'posts/small.gif')

    def test_group_pages_show_correct_context(self):
        """Шаблон group_list получает правильный контекст"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug_1'}))
        first_object = response.context['group']
        group_title = first_object.title
        group_slug = first_object.slug
        post_image = Post.objects.first().image
        self.assertEqual(post_image, 'posts/small.gif')
        self.assertEqual(group_title, 'Заголовок для тестовой группы 1')
        self.assertEqual(group_slug, 'test_slug_1')

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug_1'}))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        self.assertTrue(post_text, 'Тестовый пост автора 2')

    def test_profile_correct_context(self):
        """Шаблон profile получает правильный context"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'test_author_1'}))
        first_object = response.context['page_obj'][0]
        post_text = first_object.text
        post_author = first_object.author.username
        post_image = Post.objects.first().image
        self.assertEqual(post_image, 'posts/small.gif')
        self.assertEqual(post_author, 'test_author_1')
        self.assertEqual(post_text, 'Тестовый пост автора 1')

    def test_post_detail_correct_context(self):
        """Шаблон post_detail получает правильный context"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '101'}))
        first_object = response.context['post']
        post_text = first_object.text
        post_id = first_object.id
        post_image = Post.objects.first().image
        self.assertEqual(post_image, 'posts/small.gif')
        self.assertEqual(post_text, 'Тестовый пост автора 1')
        self.assertEqual(post_id, 101)

    def test_create_correct_context(self):
        """Шаблон create получает правильный context"""
        response = self.authorized_author_1.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон редактирования поста получает правильный context"""
        response = self.authorized_author_1.get(
            reverse('posts:post_edit', kwargs={'post_id': '101'}))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_author = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug',
            description='Тестовое описание',)
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.user_author,
                group=cls.group))
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author.force_login(self.user_author)

    def test_first_page_contains_ten_posts(self):
        list_urls = {
            reverse('posts:index_list'): 'posts/index',
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug'}): 'posts/group_list',
            reverse('posts:profile',
                    kwargs={'username': 'test_author'}): 'posts/profile',
        }
        for tested_url in list_urls.keys():
            response = self.authorized_author.get(tested_url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list), 10)

    def test_second_page_contains_three_posts(self):
        list_urls = {
            reverse('posts:index_list') + '?page=2': 'posts/index',
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug'}) + '?page=2':
            'posts/group_list',
            reverse('posts:profile',
                    kwargs={'username': 'test_author'}) + '?page=2':
            'posts/profile',
        }
        for tested_url in list_urls.keys():
            response = self.authorized_author.get(tested_url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list), 3)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_name',
                                            email='test@mail.ru',
                                            password='test_pass',),
            text='Тестовая запись для создания поста')

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='mob2556')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        """Тест кэширования страницы index.html"""
        first_state = self.authorized_client.get(reverse('posts:index_list'))
        post_1 = Post.objects.get(pk=1)
        post_1.text = 'Измененный текст'
        post_1.save()
        second_state = self.authorized_client.get(reverse('posts:index_list'))
        self.assertEqual(first_state.content, second_state.content)
        cache.clear()
        third_state = self.authorized_client.get(reverse('posts:index_list'))
        self.assertNotEqual(first_state.content, third_state.content)


class FollowTest(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для тестирования ленты'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        self.client_auth_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_following.username}
            )
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """Появляется запись в ленте подписчиков"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text = response.context["page_obj"][0].text
        self.assertEqual(post_text, 'Тестовая запись для тестирования ленты')
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(
            response,
            'Тестовая запись для тестирования ленты'
        )

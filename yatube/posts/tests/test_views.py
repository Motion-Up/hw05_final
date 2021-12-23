import tempfile
import shutil

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls.base import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache

from posts.models import Group, Post, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Наполняем БД группами и записями для тестирования
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.user = User.objects.create_user(username='ignatdan')
        for group_number in range(1, 3):
            Group.objects.create(
                title=f'Тестовая группа {group_number}',
                slug=f'test_slug_{group_number}',
                description='Тестовое описание',
            )
        for post_and_comment_number in range(1, 25):
            if post_and_comment_number < 13:
                Post.objects.create(
                    author=cls.user,
                    text=f'Тестовая группа {post_and_comment_number}',
                    group=Group.objects.get(title='Тестовая группа 1'),
                    image=SimpleUploadedFile(
                        name=f'{post_and_comment_number}.gif',
                        content=cls.small_gif,
                        content_type='image/gif'
                    )
                )
                Comment.objects.create(
                    text=f'Comment number {post_and_comment_number}',
                    author=cls.user,
                    post=Post.objects.get(id=post_and_comment_number)
                )
            else:
                Post.objects.create(
                    author=cls.user,
                    text=f'Тестовая группа {post_and_comment_number}',
                    group=Group.objects.get(title='Тестовая группа 2'),
                    image=SimpleUploadedFile(
                        name=f'{post_and_comment_number}.gif',
                        content=cls.small_gif,
                        content_type='image/gif'
                    )
                )
                Comment.objects.create(
                    text=f'Comment number {post_and_comment_number}',
                    author=cls.user,
                    post=Post.objects.get(id=post_and_comment_number)
                )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(PostsViewsTests.user)
        self.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        self.post = Post.objects.order_by('id').last()
        self.group = Group.objects.last()

    def get_response_context_page_obj(self, response):
        """Метод для получения контекста"""
        context = response.context['page_obj'][0]
        return {
            'author': context.author,
            'text': context.text,
            'group': context.group,
            'image': context.image
        }

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_reverse_dict = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_reverse_dict.items():
            with self.subTest(adress=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context_and_paginator(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = self.get_response_context_page_obj(response)
        self.assertEqual(post['author'], PostsViewsTests.user)
        self.assertEqual(post['text'], self.post.text)
        self.assertEqual(
            post['group'],
            Group.objects.get(title=self.group.title)
        )
        self.assertEqual(post['image'].name, self.post.image.name)
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=3'
        )
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_group_list_page_show_correct_context_and_paginator(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        group = response.context['group']
        post = self.get_response_context_page_obj(response)
        self.assertEqual(group, Group.objects.get(title=self.group.title))
        self.assertEqual(post['text'], self.post.text)
        self.assertEqual(post['image'].name, self.post.image.name)
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug_1'}
            ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_profile_page_show_correct_context_and_paginator(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'ignatdan'})
        )
        author = response.context['author']
        count = response.context['count']
        post = self.get_response_context_page_obj(response)
        self.assertEqual(author, PostsViewsTests.user)
        self.assertEqual(count, 24)
        self.assertEqual(post['text'], self.post.text)
        self.assertEqual(post['image'].name, self.post.image.name)
        self.assertEqual(len(response.context['page_obj']), 10)
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'ignatdan'}
            ) + '?page=3'
        )
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post = response.context['post']
        text = post.text
        count = response.context['count']
        comments = response.context['comments']
        first_comment = Comment.objects.all().filter(post=self.post)[0].text
        self.assertEqual(text, self.post.text)
        self.assertEqual(post.image.name, self.post.image.name)
        self.assertEqual(comments[0].text, first_comment)
        self.assertEqual(count, 24)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        for field, form in self.form_fields.items():
            with self.subTest(adress=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, form)

    def test_edit_post_page_show_correct_context(self):
        """Шаблон edit_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        post = response.context['post']
        text = post.text
        self.assertEqual(text, self.post.text)
        for field, form in self.form_fields.items():
            with self.subTest(adress=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, form)


class TestCache(TestCase):
    @classmethod
    def setUpClass(cls):
        # Наполняем БД группами и записями для тестирования
        super().setUpClass()
        cls.user = User.objects.create_user(username='ignatdan')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Проверка кэша'
        )

    def test_index_cache(self):
        """Провекрка кэша"""
        cache.clear()
        post_text = TestCache.post.text
        response = self.client.get(
            reverse('posts:index')
        )
        TestCache.post.delete()
        self.assertIn(post_text, response.content.decode('UTF-8'))
        cache.clear()
        response = self.client.get(
            reverse('posts:index')
        )
        self.assertNotIn(post_text, response.content.decode('UTF-8'))


class TestFollowing(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='ignatdan')
        cls.author = User.objects.create_user(username='leo')
        cls.author_for_example = User.objects.create_user(username='example')
        cls.post = Post.objects.create(
            author=cls.author,
            text='For followers!'
        )

    def setUp(self):
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(TestFollowing.user)
        self.subscribed_to_the_author = Post.objects.create(
            author=TestFollowing.author,
            text='leo'
        )
        self.not_subscribed_to_the_author = Post.objects.create(
            author=TestFollowing.author_for_example,
            text='example'
        )

    def new_subscription(self):
        Follow.objects.create(
            user=TestFollowing.user,
            author=TestFollowing.author
        )
        return TestFollowing.author

    def test_follow(self):
        count = Follow.objects.all().count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': TestFollowing.author}
            )
        )
        self.assertEqual(Follow.objects.all().count(), count + 1)

    def test_unfollow(self):
        self.new_subscription()
        Post.objects.create(author=TestFollowing.author, text='fdvkdf')
        count = Follow.objects.all().count()
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': TestFollowing.author}
            )
        )
        self.assertNotEqual(Follow.objects.all().count(), count)

    def test_new_post_for_follower(self):
        author = self.new_subscription()
        new_post_my_follow = self.subscribed_to_the_author
        new_post_not_my_follow = self.not_subscribed_to_the_author
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        page_obj = response.context['page_obj']
        self.assertEqual(page_obj[0].author, author)
        self.assertIn(new_post_my_follow, page_obj)
        self.assertNotIn(new_post_not_my_follow, page_obj)

import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Post, Group, Comment

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Group.objects.create(
            title='Test 1',
            slug='test_1',
            description='Test 1 description'
        )
        cls.user = User.objects.create_user(username='ignatdan')
        cls.post = Post.objects.create(
            text='Тестовый заголовок',
            author=cls.user
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)
        self.form_data = {
            'text': 'Тестовый заголовок 5',
            'image': SimpleUploadedFile(
                name='1.gif',
                content=self.small_gif,
                content_type='image/gif'
            )
        }
        self.form_data_with_group = {
            'text': 'Тестовый заголовок 6',
            'group': Group.objects.first().id,
            'image': SimpleUploadedFile(
                name='2.gif',
                content=self.small_gif,
                content_type='image/gif'
            )
        }
        self.form_data_comment = {
            'text': 'My first comment!',
            'author': PostCreateFormTests.user,
            'post': PostCreateFormTests.post
        }

    def test_create_post(self):
        """Подсчитаем количество записей в Post и работу redirect"""
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostCreateFormTests.user.username})
        )
        post = Post.objects.order_by('id').last()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, self.form_data['text'])
        image_content = open(
            f'{TEMP_MEDIA_ROOT}/{post.image.name}',
            'rb'
        ).read()
        self.assertEqual(image_content, self.small_gif)

    def test_edit_post(self):
        post_before_edit = Post.objects.get(id=PostCreateFormTests.post.id)
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCreateFormTests.post.id})
        )
        post = Post.objects.get(id=PostCreateFormTests.post.id)
        self.assertNotEqual(post.text, post_before_edit.text)
        image_content = open(
            f'{TEMP_MEDIA_ROOT}/{post.image.name}',
            'rb'
        ).read()
        self.assertEqual(image_content, self.small_gif)

    def test_create_post_guest_client(self):
        posts_count = Post.objects.count()
        self.client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_edit_post_guest_client(self):
        self.client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=self.form_data,
            follow=True
        )
        post = Post.objects.get(id=PostCreateFormTests.post.id)
        self.assertNotEqual(post.text, self.form_data['text'])

    def test_create_post_with_group(self):
        """Подсчитаем количество записей в Post и работу redirect"""
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data_with_group,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': PostCreateFormTests.user.username})
        )
        post = Post.objects.order_by('id').last()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.group.id, self.form_data_with_group['group'])
        self.assertEqual(post.text, self.form_data_with_group['text'])
        image_content = open(
            f'{TEMP_MEDIA_ROOT}/{post.image.name}',
            'rb'
        ).read()
        self.assertEqual(image_content, self.small_gif)

    def test_edit_post_with_group(self):
        post_before_edit = Post.objects.get(id=PostCreateFormTests.post.id)
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=self.form_data_with_group,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCreateFormTests.post.id})
        )
        post = Post.objects.get(id=PostCreateFormTests.post.id)
        self.assertNotEqual(post.text, post_before_edit.text)
        image_content = open(
            f'{TEMP_MEDIA_ROOT}/{post.image.name}',
            'rb'
        ).read()
        self.assertEqual(image_content, self.small_gif)

    def test_create_comment(self):
        """Проверяем комментарий авторизованным пользователем и редирект"""
        comments_count = Comment.objects.count()
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=self.form_data_comment,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCreateFormTests.post.id})
        )
        comment = Comment.objects.order_by('id').last()
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.author, self.form_data_comment['author'])
        self.assertEqual(comment.text, self.form_data_comment['text'])
        self.assertEqual(comment.post, self.form_data_comment['post'])

    def test_create_comment_guest_client(self):
        """Проверяем комментарий не авторизованным пользователем и редирект"""
        comments_count = Comment.objects.count()
        self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostCreateFormTests.post.id}
            ),
            data=self.form_data_comment,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        dict_models = {
            'group': PostModelTest.group,
            'post': PostModelTest.post
        }
        field_str = {
            'group': PostModelTest.group.title,
            'post': PostModelTest.post.text[:15]
        }
        for model, text in field_str.items():
            with self.subTest(field=model):
                self.assertEqual(
                    dict_models[f'{model}'].__str__(), text
                )

    def test_help_text_for_post(self):
        """Проверяем help_text для модели Post"""
        task = PostModelTest.post
        field_text_dict = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу'
        }
        for field, text in field_text_dict.items():
            with self.subTest(adress=field):
                help_text = task._meta.get_field(f'{field}').help_text
                self.assertEqual(help_text, text)

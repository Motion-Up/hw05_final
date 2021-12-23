from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls_templates_dict = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for url, template in urls_templates_dict.items():
            with self.subTest(adress=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_correct_entry_for_anonymous_client(self):
        """Проверка доступа страниц для анонимного пользователя"""
        urls_status_dict = {
            '/about/author/': 200,
            '/about/tech/': 200
        }
        for url, status in urls_status_dict.items():
            with self.subTest(adress=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, status)

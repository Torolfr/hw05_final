from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse


class AboutURLTests(TestCase):

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адреса /author/ и /tech/."""
        public_url_names = ('/about/author/', '/about/tech/')
        for url in public_url_names:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_name_path(self):
        """Проверка name path() для адреса /author/ и /tech/."""
        url_names = {
            '/about/author/': 'about:author',
            '/about/tech/': 'about:tech'
        }
        for url, name in url_names.items():
            with self.subTest(url=url):
                self.assertEqual(url, reverse(name))

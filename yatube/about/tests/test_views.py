from django.test import Client, TestCase
from django.urls import reverse


class AboutViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_accessible_by_name(self):
        """URL, генерируемый при помощи имени about:author
        и about:tech доступен."""
        templates_pages_names = ('about:author', 'about:tech')
        for name in templates_pages_names:
            response = self.guest_client.get(reverse(name))
            self.assertEqual(response.status_code, 200)

    def test_about_pages_uses_correct_template(self):
        """При запросе к about:author и about:tech
        применяется правильный шаблон."""
        templates_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

from django.test import TestCase
from django.urls import reverse


class AboutViewsTests(TestCase):

    def test_about_pages_uses_correct_template(self):
        """При запросе к about:author и about:tech
        применяется правильный шаблон."""
        templates_pages_names = {
            'about/author.html': 'about:author',
            'about/tech.html': 'about:tech',
        }
        for template, name in templates_pages_names.items():
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertTemplateUsed(response, template)

from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Проверьте, что используется шаблон core/404.html

    def test_page_correct_template(self):
        response = self.client.get('handler404')
        self.assertTemplateUsed(response, 'core/404.html')

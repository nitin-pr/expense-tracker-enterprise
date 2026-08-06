from django.test import TestCase
from common.exceptions import NotFoundError, ValidationError, app_exception_handler

class AppExceptionHandlerTests(TestCase):
    def test_app_exception_returns_structured_response(self):
        exc = NotFoundError("Expense 42 not found")
        response = app_exception_handler(exc, context={})

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["code"], "not_found")
        self.assertEqual(response.data["message"], "Expense 42 not found")

    def test_app_exception_default_message(self):
        exc = ValidationError()
        response = app_exception_handler(exc, context={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "Invalid input.")

    def test_unhandled_exception_returns_generic_500(self):
        exc = KeyError("something unexpected")
        response = app_exception_handler(exc, context={})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["code"], "server_error")
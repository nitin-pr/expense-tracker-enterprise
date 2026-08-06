from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

from django.test import TestCase

from common.exceptions import ValidationError
from common.validators import (
    validate_positive_amount,
    validate_not_future_date,
    validate_file_size_and_type,
)


class ValidatePositiveAmountTests(TestCase):
    def test_accepts_positive_amount(self):
        validate_positive_amount(Decimal("10.50"))  # should not raise

    def test_rejects_zero(self):
        with self.assertRaises(ValidationError):
            validate_positive_amount(Decimal("0"))

    def test_rejects_negative(self):
        with self.assertRaises(ValidationError):
            validate_positive_amount(Decimal("-5"))


class ValidateNotFutureDateTests(TestCase):
    def test_accepts_today(self):
        validate_not_future_date(date.today())  # should not raise

    def test_accepts_past_date(self):
        validate_not_future_date(date.today() - timedelta(days=1))  # should not raise

    def test_rejects_future_date(self):
        with self.assertRaises(ValidationError):
            validate_not_future_date(date.today() + timedelta(days=1))


class ValidateFileSizeAndTypeTests(TestCase):
    def test_accepts_valid_image(self):
        file = SimpleNamespace(content_type="image/jpeg", size=1024)
        validate_file_size_and_type(file)  # should not raise

    def test_rejects_bad_content_type(self):
        file = SimpleNamespace(content_type="application/exe", size=1024)
        with self.assertRaises(ValidationError):
            validate_file_size_and_type(file)

    def test_rejects_oversized_file(self):
        file = SimpleNamespace(content_type="image/png", size=6 * 1024 * 1024)
        with self.assertRaises(ValidationError):
            validate_file_size_and_type(file)
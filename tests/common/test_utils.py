from datetime import date

from django.test import TestCase

from common.utils import month_bounds


class MonthBoundsTests(TestCase):
    def test_regular_month(self):
        self.assertEqual(month_bounds(2026, 1), (date(2026, 1, 1), date(2026, 1, 31)))

    def test_30_day_month(self):
        self.assertEqual(month_bounds(2026, 4), (date(2026, 4, 1), date(2026, 4, 30)))

    def test_february_non_leap_year(self):
        self.assertEqual(month_bounds(2026, 2), (date(2026, 2, 1), date(2026, 2, 28)))

    def test_february_leap_year(self):
        self.assertEqual(month_bounds(2028, 2), (date(2028, 2, 1), date(2028, 2, 29)))

    def test_december(self):
        self.assertEqual(month_bounds(2026, 12), (date(2026, 12, 1), date(2026, 12, 31)))

"""Tests for utility functions in the roadmap_analyzer.utils module."""

import datetime
import unittest
from datetime import date

import pandas as pd

from roadmap_analyzer.utils import (
    add_working_days,
    convert_to_date,
    get_quarter_from_date,
    is_working_day,
    triangular_random,
)


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""

    def test_convert_to_date(self):
        """Test convert_to_date function with various input types."""
        # Test with datetime object
        dt = datetime.datetime(2025, 7, 25)
        self.assertEqual(convert_to_date(dt), date(2025, 7, 25))

        # Test with date object
        d = date(2025, 7, 25)
        self.assertEqual(convert_to_date(d), date(2025, 7, 25))

        # Test with pandas Timestamp
        ts = pd.Timestamp("2025-07-25")
        self.assertEqual(convert_to_date(ts), date(2025, 7, 25))

        # Test with string
        self.assertEqual(convert_to_date("2025-07-25"), date(2025, 7, 25))

    def test_triangular_random(self):
        """Test triangular_random function generates values within expected range."""
        min_val = 10
        mode_val = 20
        max_val = 30

        # Generate multiple values and check they're in range
        for _ in range(100):
            value = triangular_random(min_val, mode_val, max_val)
            self.assertGreaterEqual(value, min_val)
            self.assertLessEqual(value, max_val)

    def test_add_working_days(self):
        """Test add_working_days function with various scenarios."""
        # Test adding working days from a Monday
        monday = date(2025, 7, 28)  # A Monday
        self.assertEqual(add_working_days(monday, 1), date(2025, 7, 29))  # Tuesday
        self.assertEqual(add_working_days(monday, 4), date(2025, 8, 1))  # Friday
        self.assertEqual(add_working_days(monday, 5), date(2025, 8, 4))  # Next Monday (skips weekend)

        # Test adding working days from a Friday
        friday = date(2025, 7, 25)  # A Friday
        self.assertEqual(add_working_days(friday, 1), date(2025, 7, 28))  # Next Monday (skips weekend)
        self.assertEqual(add_working_days(friday, 3), date(2025, 7, 30))  # Next Wednesday

        # Test adding zero working days
        self.assertEqual(add_working_days(monday, 0), monday)

    def test_get_quarter_from_date(self):
        """Test get_quarter_from_date function for different dates."""
        # Test each quarter
        self.assertEqual(get_quarter_from_date(date(2025, 1, 15)), "2025-Q1")
        self.assertEqual(get_quarter_from_date(date(2025, 4, 15)), "2025-Q2")
        self.assertEqual(get_quarter_from_date(date(2025, 7, 15)), "2025-Q3")
        self.assertEqual(get_quarter_from_date(date(2025, 10, 15)), "2025-Q4")

        # Test quarter boundaries
        self.assertEqual(get_quarter_from_date(date(2025, 3, 31)), "2025-Q1")
        self.assertEqual(get_quarter_from_date(date(2025, 4, 1)), "2025-Q2")

    def test_is_working_day(self):
        """Test is_working_day function for weekdays and weekends."""
        # Test weekdays (Monday to Friday)
        monday = date(2025, 7, 28)
        tuesday = date(2025, 7, 29)
        wednesday = date(2025, 7, 30)
        thursday = date(2025, 7, 31)
        friday = date(2025, 8, 1)

        self.assertTrue(is_working_day(monday))
        self.assertTrue(is_working_day(tuesday))
        self.assertTrue(is_working_day(wednesday))
        self.assertTrue(is_working_day(thursday))
        self.assertTrue(is_working_day(friday))

        # Test weekends (Saturday and Sunday)
        saturday = date(2025, 7, 26)
        sunday = date(2025, 7, 27)

        self.assertFalse(is_working_day(saturday))
        self.assertFalse(is_working_day(sunday))

        # Test with pandas Timestamp
        self.assertTrue(is_working_day(pd.Timestamp(monday)))
        self.assertFalse(is_working_day(pd.Timestamp(saturday)))


if __name__ == "__main__":
    unittest.main()

"""Unit tests for input validation utilities."""

import unittest

from mcp_govt_api.utils.validation import (
    validate_date,
    validate_latitude,
    validate_limit,
    validate_longitude,
    validate_magnitude,
    validate_state_code,
)


class TestValidateLimit(unittest.TestCase):
    """Tests for validate_limit."""

    def test_default_when_none(self):
        self.assertEqual(validate_limit(None), 10)

    def test_custom_default(self):
        self.assertEqual(validate_limit(None, default=5), 5)

    def test_within_range(self):
        self.assertEqual(validate_limit(50), 50)

    def test_clamp_below_one(self):
        self.assertEqual(validate_limit(0), 1)
        self.assertEqual(validate_limit(-5), 1)

    def test_clamp_above_max(self):
        self.assertEqual(validate_limit(200, max_val=100), 100)

    def test_custom_max(self):
        self.assertEqual(validate_limit(500, max_val=20000), 500)
        self.assertEqual(validate_limit(30000, max_val=20000), 20000)

    def test_boundary_values(self):
        self.assertEqual(validate_limit(1), 1)
        self.assertEqual(validate_limit(100), 100)

    def test_non_integer_raises(self):
        with self.assertRaises(ValueError):
            validate_limit("ten")
        with self.assertRaises(ValueError):
            validate_limit(3.5)


class TestValidateStateCode(unittest.TestCase):
    """Tests for validate_state_code."""

    def test_valid_states(self):
        self.assertEqual(validate_state_code("CA"), "CA")
        self.assertEqual(validate_state_code("tx"), "TX")
        self.assertEqual(validate_state_code("ny"), "NY")

    def test_dc_and_territories(self):
        self.assertEqual(validate_state_code("DC"), "DC")
        self.assertEqual(validate_state_code("PR"), "PR")
        self.assertEqual(validate_state_code("GU"), "GU")

    def test_whitespace_stripped(self):
        self.assertEqual(validate_state_code(" CA "), "CA")

    def test_invalid_code(self):
        with self.assertRaises(ValueError):
            validate_state_code("ZZ")

    def test_too_long(self):
        with self.assertRaises(ValueError):
            validate_state_code("CAL")

    def test_too_short(self):
        with self.assertRaises(ValueError):
            validate_state_code("C")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            validate_state_code("")

    def test_non_string(self):
        with self.assertRaises(ValueError):
            validate_state_code(42)


class TestValidateDate(unittest.TestCase):
    """Tests for validate_date."""

    def test_valid_date(self):
        self.assertEqual(validate_date("2024-01-15"), "2024-01-15")

    def test_custom_format(self):
        self.assertEqual(
            validate_date("01/15/2024", fmt="%m/%d/%Y"), "01/15/2024"
        )

    def test_whitespace_stripped(self):
        self.assertEqual(validate_date(" 2024-01-15 "), "2024-01-15")

    def test_invalid_format(self):
        with self.assertRaises(ValueError):
            validate_date("15-01-2024")

    def test_invalid_date_values(self):
        with self.assertRaises(ValueError):
            validate_date("2024-13-01")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            validate_date("")

    def test_non_string(self):
        with self.assertRaises(ValueError):
            validate_date(20240115)


class TestValidateLatitude(unittest.TestCase):
    """Tests for validate_latitude."""

    def test_valid_values(self):
        self.assertEqual(validate_latitude(0), 0.0)
        self.assertEqual(validate_latitude(45.5), 45.5)
        self.assertEqual(validate_latitude(-90), -90.0)
        self.assertEqual(validate_latitude(90), 90.0)

    def test_string_number(self):
        self.assertEqual(validate_latitude("38.8894"), 38.8894)

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_latitude(91)
        with self.assertRaises(ValueError):
            validate_latitude(-91)

    def test_non_numeric(self):
        with self.assertRaises(ValueError):
            validate_latitude("abc")
        with self.assertRaises(ValueError):
            validate_latitude(None)


class TestValidateLongitude(unittest.TestCase):
    """Tests for validate_longitude."""

    def test_valid_values(self):
        self.assertEqual(validate_longitude(0), 0.0)
        self.assertEqual(validate_longitude(-77.0352), -77.0352)
        self.assertEqual(validate_longitude(-180), -180.0)
        self.assertEqual(validate_longitude(180), 180.0)

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_longitude(181)
        with self.assertRaises(ValueError):
            validate_longitude(-181)

    def test_non_numeric(self):
        with self.assertRaises(ValueError):
            validate_longitude("abc")


class TestValidateMagnitude(unittest.TestCase):
    """Tests for validate_magnitude."""

    def test_valid_values(self):
        self.assertEqual(validate_magnitude(0), 0.0)
        self.assertEqual(validate_magnitude(4.5), 4.5)
        self.assertEqual(validate_magnitude(10), 10.0)

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            validate_magnitude(-1)
        with self.assertRaises(ValueError):
            validate_magnitude(11)

    def test_non_numeric(self):
        with self.assertRaises(ValueError):
            validate_magnitude("big")


if __name__ == "__main__":
    unittest.main()

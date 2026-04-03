"""Tests for utility functions in core/core_utils.py"""

import pytest
from datetime import datetime

from core.core_utils import (
    str2bool, normalize_with_microsecs, doyToIsoZ, get_now_isoZ,
    iso_to_datetime, doy_to_datetime, str_to_datetime,
    datetime_to_doy, datetime_to_isoZ, validate_time, get_hostname,
    VenueType, TimeParsingError, get_utc, get_utc_iso
)


class TestStr2Bool:
    def test_true_string(self):
        assert str2bool('true') is True

    def test_false_string(self):
        assert str2bool('false') is False

    def test_true_string_uppercase(self):
        assert str2bool('True') is True

    def test_false_string_uppercase(self):
        assert str2bool('False') is False

    def test_bool_true(self):
        assert str2bool(True) is True

    def test_bool_false(self):
        assert str2bool(False) is False

    def test_arbitrary_string_returns_false(self):
        assert str2bool('yes') is False

    def test_empty_string_returns_false(self):
        assert str2bool('') is False


class TestNormalizeWithMicrosecs:
    def test_nanosecond_precision_truncated(self):
        result = normalize_with_microsecs('2024-100T12:00:00.123456789')
        assert result == '2024-100T12:00:00.123456'

    def test_microsecond_precision_preserved(self):
        result = normalize_with_microsecs('2024-100T12:00:00.123456')
        assert result == '2024-100T12:00:00.123456'

    def test_millisecond_precision_preserved(self):
        result = normalize_with_microsecs('2024-100T12:00:00.123')
        assert result == '2024-100T12:00:00.123'

    def test_exact_second_adds_zeros(self):
        result = normalize_with_microsecs('2024-100T12:00:00')
        assert result == '2024-100T12:00:00.000000'


class TestDoyToIsoZ:
    def test_basic_conversion(self):
        result = doyToIsoZ('2024-100T12:00:00.000000')
        assert result == '2024-04-09T12:00:00.000Z'

    def test_with_microseconds(self):
        result = doyToIsoZ('2024-001T00:00:00.123456')
        assert result == '2024-01-01T00:00:00.123Z'


class TestGetNowIsoZ:
    def test_format(self):
        result = get_now_isoZ()
        assert result.endswith('Z')
        assert 'T' in result
        # Should be parseable as ISO datetime (without Z)
        datetime.strptime(result[:-1], '%Y-%m-%dT%H:%M:%S.%f')


class TestIsoToDatetime:
    def test_with_z_and_microsecs(self):
        dt = iso_to_datetime('2024-04-10T12:00:00.123456Z')
        assert dt.year == 2024
        assert dt.month == 4
        assert dt.day == 10
        assert dt.hour == 12

    def test_with_z_no_microsecs(self):
        dt = iso_to_datetime('2024-04-10T12:00:00Z')
        assert dt.second == 0

    def test_without_z_with_microsecs(self):
        dt = iso_to_datetime('2024-04-10T12:00:00.123456')
        assert dt.microsecond == 123456

    def test_without_z_no_microsecs(self):
        dt = iso_to_datetime('2024-04-10T12:00:00')
        assert dt.microsecond == 0

    def test_must_have_z_raises_without_z(self):
        with pytest.raises(ValueError):
            iso_to_datetime('2024-04-10T12:00:00', must_have_Z=True)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            iso_to_datetime('not-a-date')


class TestDoyToDatetime:
    def test_with_microsecs(self):
        dt = doy_to_datetime('2024-100T12:30:45.123456')
        assert dt.year == 2024
        assert dt.hour == 12
        assert dt.minute == 30

    def test_without_microsecs(self):
        dt = doy_to_datetime('2024-100T12:30:45')
        assert dt.second == 45

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            doy_to_datetime('not-a-date')


class TestStrToDatetime:
    def test_iso_format(self):
        dt = str_to_datetime('2024-04-10T12:00:00')
        assert dt.year == 2024

    def test_doy_format(self):
        dt = str_to_datetime('2024-100T12:00:00')
        assert dt.year == 2024

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            str_to_datetime('not-a-date')


class TestDatetimeToDoy:
    def test_no_resolution(self):
        dt = datetime(2024, 4, 10, 12, 0, 0)
        result = datetime_to_doy(dt)
        assert result == '2024-101T12:00:00'

    def test_millis_resolution(self):
        dt = datetime(2024, 4, 10, 12, 0, 0, 123456)
        result = datetime_to_doy(dt, res='millis')
        assert result == '2024-101T12:00:00.123'

    def test_micros_resolution(self):
        dt = datetime(2024, 4, 10, 12, 0, 0, 123456)
        result = datetime_to_doy(dt, res='micros')
        assert result == '2024-101T12:00:00.123456'


class TestDatetimeToIsoZ:
    def test_no_resolution(self):
        dt = datetime(2024, 4, 10, 12, 0, 0)
        result = datetime_to_isoZ(dt)
        assert result == '2024-04-10T12:00:00'

    def test_millis_resolution(self):
        dt = datetime(2024, 4, 10, 12, 0, 0, 123456)
        result = datetime_to_isoZ(dt, res='millis')
        assert result == '2024-04-10T12:00:00.123'


class TestValidateTime:
    def test_doy_with_microsecs(self):
        time_type, converted = validate_time('2024-100T12:00:00.123456')
        assert time_type == 'SCET'

    def test_doy_without_microsecs(self):
        time_type, converted = validate_time('2024-100T12:00:00')
        assert time_type == 'SCET'

    def test_iso_without_microsecs(self):
        time_type, converted = validate_time('2024-04-10T12:00:00')
        assert time_type == 'SCET'

    def test_iso_with_microsecs(self):
        time_type, converted = validate_time('2024-04-10T12:00:00.123456')
        assert time_type == 'SCET'

    def test_sclk_float(self):
        time_type, converted = validate_time('12345.6789')
        assert time_type == 'SCLK'
        assert converted == 12345.6789

    def test_sclk_coarse_fine(self):
        # Note: validate_time() has a known issue where converted_time is not
        # set for SCLK coarse-fine format (e.g. "1234567-12345"). It recognizes
        # the format as SCLK but raises UnboundLocalError on the return.
        with pytest.raises(UnboundLocalError):
            validate_time('1234567-12345')

    def test_invalid_raises(self):
        with pytest.raises(TimeParsingError):
            validate_time('not-a-time')


class TestGetHostname:
    def test_returns_string(self):
        hostname = get_hostname()
        assert isinstance(hostname, str)
        assert len(hostname) > 0


class TestVenueType:
    def test_enum_values(self):
        assert VenueType.WSTS.value == 'WSTS'
        assert VenueType.TESTBED.value == 'TESTBED'
        assert VenueType.ATLO.value == 'ATLO'


class TestGetUtc:
    def test_returns_datetime(self):
        result = get_utc()
        assert isinstance(result, datetime)

    def test_get_utc_iso_returns_string(self):
        result = get_utc_iso()
        assert isinstance(result, str)
        assert 'T' in result

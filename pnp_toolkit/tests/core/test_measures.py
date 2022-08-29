from pnp_toolkit.core import measures
import math
import pytest


@pytest.mark.parametrize(
    "measure_str,expected_value,expected_unit",
    [
        ("10.2inch", 10.2, "inch"),
        (" 5.111 mm  ", 5.111, "mm"),
        ("5 in", 5, "in"),
        ("7", 7.0, None),
    ],
)
def test_parse_raw_measure(measure_str, expected_value, expected_unit):
    raw_measure = measures._parse_raw_measure(measure_str)
    assert raw_measure == (expected_value, expected_unit)


@pytest.mark.parametrize(
    "base_value,base_unit,expected_value,expected_unit",
    [
        (10.2, "inch", 10.2, "inch"),
        (10.0, "inch", 254.0, "mm"),
        (1.5, "m", 1500, "mm"),
    ],
)
def test_convert_raw_measure_to_unit(
    base_value, base_unit, expected_value, expected_unit
):
    actual_value = measures._convert_raw_measure_to_unit(
        base_value, base_unit, expected_unit
    )
    _assert_float(actual_value, expected_value)


@pytest.mark.parametrize(
    "measure_pair,expected_pair",
    [
        ("10.2 inch * 1 inch", (10.2, 1)),
        ("1.5mm*2mm", (0.0590551, 0.0787402)),
        ("15.2*10.5mm", (0.5984252, 0.4133858)),
    ],
)
def test_parse_pair_inches(measure_pair, expected_pair):
    inch_first, inch_second = measures.parse_pair_inches(measure_pair)
    _assert_float(inch_first, expected_pair[0])
    _assert_float(inch_second, expected_pair[1])


@pytest.mark.parametrize(
    "measure_pair,expected_pair",
    [
        ("10.2 inch * 1 inch", (259.08, 25.4)),
        ("1.5mm*2mm", (1.5, 2)),
        ("15.2*10.5mm", (15.2, 10.5)),
    ],
)
def test_parse_pair_mm(measure_pair, expected_pair):
    mm_first, mm_second = measures.parse_pair_mm(measure_pair)
    _assert_float(mm_first, expected_pair[0])
    _assert_float(mm_second, expected_pair[1])


def _assert_float(actual, expected):
    _FLOAT_DELTA = 0.00001
    assert math.isclose(actual, expected, rel_tol=_FLOAT_DELTA)

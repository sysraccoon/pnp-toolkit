import math
from typing import Tuple

import pytest

from pnp_toolkit.core.spec.generic_parse import parse_version, resolve_variable


@pytest.mark.parametrize(
    "raw_version,expected_version",
    [
        ("1.0", (1, 0)),
        ("0.45", (0, 45)),
        ("2.2", (2, 2)),
    ],
)
def test_parse_version(raw_version: str, expected_version: Tuple[int, int]):
    actual_version = parse_version(raw_version)
    assert actual_version == expected_version


@pytest.mark.parametrize(
    "template, variables, expected_value",
    [
        (
            "str without variables",
            {
                "x": "sample",
            },
            "str without variables",
        ),
        (
            "path/with/single/variable/{{x}}",
            {
                "x": "simple_replacement_work",
            },
            "path/with/single/variable/simple_replacement_work",
        ),
        (
            "multiple variables {{x}}, {{y}}",
            {
                "x": "sample1",
                "y": "sample2",
            },
            "multiple variables sample1, sample2",
        ),
    ],
)
def test_resolve_variable(template: str, variables: dict, expected_value: str):
    actual_value = resolve_variable(template, variables)
    assert actual_value == expected_value


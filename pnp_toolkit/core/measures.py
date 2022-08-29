import re
import typing

DEFAULT_MEASURE = "mm"


def parse_inches(measure: str) -> float:
    value, unit = _parse_raw_measure(measure)
    inches = _convert_raw_measure_to_unit(value, unit, "inches")
    return inches


def parse_mm(measure: str) -> float:
    value, unit = _parse_raw_measure(measure)
    millimetres = _convert_raw_measure_to_unit(value, unit, "millimetres")
    return millimetres


def parse_pair_inches(measure_pair: str) -> typing.Tuple[float, float]:
    first_measure, second_measure = _parse_raw_pair(measure_pair)
    first_inches = _convert_raw_measure_to_unit(*first_measure, "inches")
    second_inches = _convert_raw_measure_to_unit(*second_measure, "inches")
    return first_inches, second_inches


def parse_pair_mm(measure_pair: str) -> typing.Tuple[float, float]:
    first_measure, second_measure = _parse_raw_pair(measure_pair)
    first_mm = _convert_raw_measure_to_unit(*first_measure, "millimetres")
    second_mm = _convert_raw_measure_to_unit(*second_measure, "millimetres")
    return first_mm, second_mm


def _parse_raw_measure(measure: str):
    measure = measure.strip()
    match = re.match(r"(?P<value>\d+(.\d+)?)\s*(?P<unit>\w*)?", measure)
    return float(match["value"]), match["unit"] or None


def _parse_raw_pair(measure_pair: str):
    DELIMITER = "*"
    splitted = measure_pair.split(DELIMITER)
    if len(splitted) != 2:
        raise ValueError(
            f"Expected two measures delimited with ({DELIMITER}) character"
        )

    first_measure = _parse_raw_measure(splitted[0])
    second_measure = _parse_raw_measure(splitted[1])

    # If unit specified only for second measure, need use it as default
    if not first_measure[1] and second_measure[1]:
        first_measure = (first_measure[0], second_measure[1])

    return first_measure, second_measure


_UNIT_ALIASES = {
    "mm": "millimetres",
    "cm": "centimetres",
    "m": "metres",
    "inch": "inches",
    "in": "inches",
    "ft": "feet",
}


def _resolve_unit(unit: typing.Optional[str]):
    if not unit:
        unit = DEFAULT_MEASURE
    return _UNIT_ALIASES.get(unit, unit)


_MEASURE_CONVERSATIONS = {
    "inches": 1.0,
    "feet": 0.0833333333,
    "millimetres": 25.4,
    "centimetres": 2.54,
    "metres": 0.0254,
}


def _convert_raw_measure_to_unit(value, base_unit, target_unit):
    base_unit_unaliased = _resolve_unit(base_unit)
    target_unit_unaliased = _resolve_unit(target_unit)

    base_conversation_value = _MEASURE_CONVERSATIONS.get(base_unit_unaliased)
    target_conversation_value = _MEASURE_CONVERSATIONS.get(target_unit_unaliased)

    if base_conversation_value is None:
        raise ValueError(f"unsupported base unit type ({base_unit})")

    if target_unit_unaliased is None:
        raise ValueError(f"unsupported target unit type ({target_unit})")

    target_value = (target_conversation_value / base_conversation_value) * value

    return target_value

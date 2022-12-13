import re
import typing
from dataclasses import dataclass

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


def _parse_n_dimension_raw_measure(n_measure: str, dimension_count: int):
    DELIMITER = "*"
    splitted = n_measure.split(DELIMITER)
    if len(splitted) != dimension_count:
        raise ValueError(f"Fail to parse '{n_measure}'. Expected {dimension_count} measures delimited with '{DELIMITER}' character")

    parsed_measures = []
    for s in splitted:
        raw_measure = _parse_raw_measure(s)
        raw_measure_unit = raw_measure[1]

        if raw_measure_unit:
            raw_measure_unit = _UNIT_ALIASES.get(raw_measure_unit, raw_measure_unit)

            if raw_measure_unit not in _MEASURE_CONVERSATIONS:
                raise ValueError(f"Fail to parse '{n_measure}'. Unsupported measure unit '{raw_measure_unit}'")

        parsed_measures.append(raw_measure)

    specified_measure_count = len([unit for _, unit in parsed_measures if unit])

    # check if all dimensions specify measure unit
    if specified_measure_count == dimension_count:
        return parsed_measures

    # check if all dimensions not specify measure unit
    if specified_measure_count == 0:
        return [(value, DEFAULT_MEASURE) for value, _ in parsed_measures]

    # check if only last specify measure
    last_measure_unit = parsed_measures[-1][1]
    if specified_measure_count == 1 and last_measure_unit:
        return [(value, last_measure_unit) for value, _ in parsed_measures]

    raise ValueError(
        f"Fail to parse '{n_measure}'. "
        f"Incorrect unit specification, declare unit type for all parts explicit (or only for last)"
    )


def _convert_n_dimension_parsed_raw_measure_to_dict(parsed_raw_measure, dimension_names: typing.List[str]):
    result = {}
    for i, (value, unit) in enumerate(parsed_raw_measure):
        dimension_name = dimension_names[i]
        result[dimension_name] = value
        result[f"{dimension_name}_unit"] = unit

    return result


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

    base_conversation_value = float(_MEASURE_CONVERSATIONS.get(base_unit_unaliased))
    target_conversation_value = float(_MEASURE_CONVERSATIONS.get(target_unit_unaliased))

    if base_conversation_value is None:
        raise ValueError(f"unsupported base unit type ({base_unit})")

    if target_unit_unaliased is None:
        raise ValueError(f"unsupported target unit type ({target_unit})")

    target_value = (target_conversation_value / base_conversation_value) * float(value)

    return target_value


def n_dimensional_parse_and_convert(dimensions: typing.List[str]):
    def wrapper(cls):
        def convert_to(self, measure_unit: str):
            return _convert_n_dimension_distance_measure(self, dimensions, type(self), measure_unit)
        cls.convert_to = convert_to

        def parse_from(cls, raw: str):
            parsed = _parse_n_dimension_raw_measure(raw, dimension_count=len(dimensions))
            parsed_dict = _convert_n_dimension_parsed_raw_measure_to_dict(parsed, dimensions)
            return cls(**parsed_dict)
        cls.parse_from = classmethod(parse_from)

        def to_mm(self):
            return self.convert_to("millimetres")
        cls.to_mm = to_mm

        def to_inch(self):
            return self.convert_to("inches")
        cls.to_inch = to_inch

        return cls

    return wrapper


def _convert_n_dimension_distance_measure(measure, dimension_names, convert_type, target_unit_name):
    converted_dimensions = {}
    converted_dimension_units = {}
    for dimension in dimension_names:
        dimension_value = getattr(measure, dimension)
        dimension_unit_field = f"{dimension}_unit"
        dimension_unit = getattr(measure, dimension_unit_field)

        converted_value = _convert_raw_measure_to_unit(dimension_value, dimension_unit, target_unit_name)
        converted_dimensions[dimension] = converted_value
        converted_dimension_units[dimension_unit_field] = dimension

    return convert_type(**converted_dimensions, **converted_dimension_units)


@n_dimensional_parse_and_convert(["x"])
@dataclass
class DistanceMeasure1D:
    x: float
    x_unit: str = DEFAULT_MEASURE


@n_dimensional_parse_and_convert(["x", "y"])
@dataclass
class DistanceMeasure2D:
    x: float
    y: float
    x_unit: str = DEFAULT_MEASURE
    y_unit: str = DEFAULT_MEASURE


@n_dimensional_parse_and_convert(["x", "y", "z", "w"])
@dataclass
class DistanceMeasure4D:
    x: float
    y: float
    z: float
    w: float
    x_unit: str = DEFAULT_MEASURE
    y_unit: str = DEFAULT_MEASURE
    z_unit: str = DEFAULT_MEASURE
    w_unit: str = DEFAULT_MEASURE

import json
import re
from typing import Tuple, Type

from pnp_toolkit.core.measures import DistanceMeasure4D, DistanceMeasure2D, DistanceMeasure1D
from pnp_toolkit.core.spec.base import PaperSpecification, PackStrategySpecification, OutputRendererSpecification


def parse_version(version: str) -> Tuple[int, int]:
    parts = version.split(".")
    if len(parts) != 2:
        raise ValueError(
            "Incorrect version format. Expected two parts (major and minor) "
            "delimited with '.'. As example '1.0'"
        )

    return int(parts[0]), int(parts[1])


def resolve_variable(value, variables: dict, expected_type: Type = str):
    value = str(value)
    used_variables = re.findall(r"{{(\w+)}}", value)
    for used in used_variables:
        variable_value = variables.get(used)
        if variable_value is None:
            raise ValueError(f"variable with name '{used}' not found. Context: {json.dumps(variables)}")
        value = value.replace("{{" + used + "}}", variable_value)
    return expected_type(value)


def _get_builtin_paper_sizes():
    paper_specs = {}
    default_paper_padding = "5*5*5*5mm"

    simple_paper_sizes = {
        "letter": "8.5*11inch",

        "a6": "105*148mm",
        "a5": "148*210mm",
        "a4": "210*297mm",
        "a3": "297*420mm",
        "a2": "420*594mm",
        "a1": "594*841mm",
        "a0": "841*1189mm",

        "sra6": "160*112mm",
        "sra5": "225*160mm",
        "sra4": "320*225mm",
        "sra3": "450*320mm",
        "sra2": "640*350mm",
        "sra1": "900*640mm",
        "sra0": "1280*900mm",
    }

    for paper_name, paper_size in simple_paper_sizes.items():
        parsed_size = DistanceMeasure2D.parse_from(paper_size)

        paper_specs[paper_name] = PaperSpecification(
            name=paper_name,
            type="simple",
            type_params={
                "size": paper_size,
                "padding": default_paper_padding,
            },
        )

        # portrait orientation is just alias to original definition
        portrait_paper_name = paper_name + "_portrait"
        paper_specs[portrait_paper_name] = paper_specs[paper_name]

        landscape_paper_name = paper_name + "_landscape"
        landscape_paper_size = f"{parsed_size.y}{parsed_size.y_unit}*{parsed_size.x}{parsed_size.x_unit}"

        paper_specs[landscape_paper_name] = PaperSpecification(
            name=landscape_paper_name,
            type="simple",
            type_params={
                "size": landscape_paper_size,
                "padding": default_paper_padding,
            },
        )

    roll_paper_sizes = [11, 17, 18, 22, 24, 30, 34, 36, 42] # all inches

    for roll_size in roll_paper_sizes:
        paper_name = f"roll_{roll_size}inch"
        paper_specs[paper_name] = PaperSpecification(
            name=paper_name,
            type="roll",
            type_params={
                "width": f"{roll_size}inch",
                "padding": default_paper_padding,
            },
        )

    return paper_specs


DEFAULT_PAPER_SPECIFICATIONS = _get_builtin_paper_sizes()


def _get_builtin_pack_strategies():
    return {
        "simple_guillotine": PackStrategySpecification(
            name="simple_guillotine",
            params={
                "rotation": True,
            },
        ),
        "roll_guillotine": PackStrategySpecification(
            name="roll_guillotine",
            params={},
        ),
    }


DEFAULT_PACK_STRATEGIES = _get_builtin_pack_strategies()


def _get_builtin_output_renderers():
    return {
        "pdf": OutputRendererSpecification(
            name="pdf",
            params={},
        ),
    }


DEFAULT_OUTPUT_RENDERERS = _get_builtin_output_renderers()

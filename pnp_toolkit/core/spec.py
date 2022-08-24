import yaml
import attr
import re

from pathlib import Path
from typing import List, Dict, Tuple, Optional

from pnp_toolkit.core.structs import Size, PaperSpec, Offset
from pnp_toolkit.core.measures import parse_pair_mm
from pnp_toolkit.core.utils import join_pathes, pnp_toolkit_path

GLOB_PATH = str

DEFAULT_PAPER_OFFSET = "5*5mm"
DEFAULT_PAPER_SPECS = {
    "letter": {"size": "8.5*11inch"},
    "A6": {"size": "105*148mm"},
    "A5": {"size": "148*210mm"},
    "A4": {"size": "210*297mm"},
    "A3": {"size": "297*420mm"},
    "A2": {"size": "420*594mm"},
}

DEFAULT_SRC_GROUPS = {
    "default": ["."],
}

DEFAULT_CARD_SIZE = "63*88mm" # mtg card size

@attr.frozen
class PDFBuildSpecification:
    @attr.frozen
    class Options:
        parallel: int
        src_dir: str
        out_dir: str

    @attr.frozen
    class LayoutSpec:
        file_name: str
        size: Size
        src_pathes: List[GLOB_PATH]
        background_pattern: Optional[str]
        background_border: bool
        multiple_copies: List[Tuple[str, int]]
        mirror: bool
        special_paper_used: List[str]
    
    variables: Dict[str, str]
    options: Options
    paper_specs: Dict[str, PaperSpec]
    paper_used: List[str]
    src_groups: Dict[str, List[GLOB_PATH]]
    layout_specs: Dict[str, LayoutSpec]

    @classmethod
    def from_dict(cls, conf: dict):
        variables = conf.get("variables", {})

        options = conf.get("options", {})
        parsed_options = cls.Options(
            parallel = cls._resolve_variable(options.get("parallel", 1), variables, expected_type=int),
            src_dir = cls._resolve_variable(options.get("src_dir", "."), variables, expected_type=str),
            out_dir = cls._resolve_variable(options.get("out_dir", "./out"), variables, expected_type=str),
        )

        custom_paper_specs = conf.get("paper_specs")
        if custom_paper_specs:
            paper_specs = {**DEFAULT_PAPER_SPECS, **custom_paper_specs}
        else:
            paper_specs = DEFAULT_PAPER_SPECS
        for paper_name, paper_spec in paper_specs.items():
            offsets = cls._parse_size(paper_spec.get("offsets", DEFAULT_PAPER_OFFSET), variables)
            horizontal_offsets, vertical_offsets = offsets.width_mm, offsets.height_mm
            paper_size = cls._parse_size(paper_spec["size"], variables)
            special = cls._parse_bool(paper_spec.get("special", False), variables)
            paper_specs[paper_name] = PaperSpec(paper_size, Offset(vertical_offsets, horizontal_offsets, vertical_offsets, horizontal_offsets), special)

        paper_used = conf.get("paper_used", ["A4"])

        src_groups = {}
        raw_src_groups = conf.get("src_groups", DEFAULT_SRC_GROUPS).items()
        for group_name, group_pathes in raw_src_groups:
            parsed_glob_pathes = cls._parse_glob_pathes(group_pathes, variables)
            src_groups[group_name] = parsed_glob_pathes

        layout_specs = {}
        for layout_name, layout_spec in conf["layout_specs"].items():
            file_name = cls._resolve_variable(layout_spec.get("file_name", f"{layout_name}.pdf"), variables, expected_type=str)
            size = cls._parse_size(layout_spec.get("size", DEFAULT_CARD_SIZE), variables)
            src_pathes = cls._parse_glob_pathes(layout_spec["src_pathes"], variables)
            multiple_copies = []
            raw_multiple_copies = layout_spec.get("multiple_copies", [])
            for copy_regex, copy_count in raw_multiple_copies:
                resolved_regex = cls._resolve_variable(copy_regex, variables)
                resolved_count = cls._resolve_variable(copy_count, variables, expected_type=int)
                multiple_copies.append((resolved_regex, resolved_count))
            background_pattern = cls._resolve_variable(layout_spec.get("background_pattern", ""), variables)
            background_border = cls._parse_bool(layout_spec.get("background_border", True), variables)
            mirror = cls._parse_bool(layout_spec.get("mirror", False), variables)
            special_paper_used = []
            for special_paper_name in layout_spec.get("special_paper_used", []):
                special_paper_used.append(cls._resolve_variable(special_paper_name, variables))

            layout_specs[layout_name] = cls.LayoutSpec(
                file_name = file_name,
                size = size,
                src_pathes = src_pathes,
                background_pattern = background_pattern,
                background_border = background_border,
                multiple_copies = multiple_copies,
                mirror = mirror,
                special_paper_used = special_paper_used,
            )

        config = cls(
            variables = variables,
            options = parsed_options,
            paper_specs = paper_specs,
            paper_used = paper_used,
            src_groups = src_groups,
            layout_specs = layout_specs,
        )

        return config
    
    @staticmethod
    def _resolve_variable(value, variables, expected_type=str):
        value = str(value)
        used_variables = re.findall(r"{{(\w+)}}", value)
        for used in used_variables:
            variable_value = variables.get(used)
            if variable_value is None:
                raise ValueError(f"variable with name {used} not found")
            value = value.replace("{{" + used + "}}", variable_value)
        return expected_type(value)

    @staticmethod
    def _parse_glob_pathes(glob_pathes, variables):
        parsed_pathes = []
        glob_pathes = glob_pathes or []
        for glob_path in glob_pathes:
            resolved_glob_path = PDFBuildSpecification._resolve_variable(glob_path, variables)
            parsed_pathes.append(resolved_glob_path)
        return parsed_pathes

    @staticmethod
    def _parse_size(value, variables):
        resolved_size = PDFBuildSpecification._resolve_variable(value, variables)
        width_mm, height_mm = parse_pair_mm(resolved_size)
        return Size(width_mm, height_mm)

    @staticmethod
    def _parse_bool(value, variables):
        bool_str = PDFBuildSpecification._resolve_variable(value, variables)
        return bool_str.lower() in ["true", "enable"]


def load_custom_spec(spec_path: str):
    return _load_spec(spec_path)


def load_built_in_spec(spec_path: str):
    builtin_spec_path = join_pathes(pnp_toolkit_path(), "builtin_specs", spec_path)
    return _load_spec(builtin_spec_path)


def _load_spec(spec_path):
    with Path(spec_path).open() as config_file:
        config_dict = yaml.load(config_file, Loader=yaml.FullLoader)
    return PDFBuildSpecification.from_dict(config_dict)

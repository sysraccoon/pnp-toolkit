from pathlib import Path
from typing import List, Union

import yaml

from pnp_toolkit.core.measures import DistanceMeasure2D
from pnp_toolkit.core.spec.base import BGSpecification, MultiGlob, OutputSpecification, ComponentSpecification, \
    DocumentSpecification, PaperSpecification, PackStrategySpecification, FrontImageSpecification, \
    BackImageSpecification
from pnp_toolkit.core.spec.generic_parse import parse_version, resolve_variable, DEFAULT_PAPER_SPECIFICATIONS, \
    DEFAULT_PACK_STRATEGIES, DEFAULT_OUTPUT_RENDERERS


def parse_from_yaml(yaml_content: str):
    content = yaml.safe_load(yaml_content)

    version = parse_version(content["spec_version"])
    if version != (1, 0):
        raise ValueError("Unsupported specification version. Expected '1.0'. "
                         "Update to new version of pnp-toolkit or downgrade specification version")

    project_name = content.get("project_name", "project_name")

    variables = content.get("variables", {})

    output_info = _parse_output_info(content.get("output", {}), variables)

    document_defaults = content.get("document_defaults", {})

    documents = _parse_multi_document_specification(content["documents"], document_defaults, variables)

    return BGSpecification(
        spec_version=version,
        project_name=project_name,
        variables=variables,
        output=output_info,
        document_defaults=document_defaults,
        documents=documents,
    )


def _parse_output_info(raw_output_info: dict, variables: dict):
    output_directory = resolve_variable(raw_output_info.get("directory", "out"), variables, expected_type=Path)
    output_format = raw_output_info.get("format", "{{file_name}}")

    return OutputSpecification(
        directory=output_directory,
        format=output_format,
    )


def _parse_multi_document_specification(documents: List[dict], defaults: dict, variables: dict):
    return [_parse_document_specification(doc, defaults, variables) for doc in documents]


def _parse_document_specification(document_spec_raw: dict, defaults: dict, variables: dict):
    document_name = document_spec_raw.get("name") or defaults.get("name") or "undefined_doc"

    raw_document_src = _resolve_multi_glob_variable(document_spec_raw.get("src") or defaults.get("src"), variables)
    document_src = MultiGlob(raw_document_src)

    document_components = _parse_multi_component_specification(
        document_spec_raw.get("components") or defaults.get("components"),
        variables,
    )

    paper = _parse_paper_specification(
        document_spec_raw.get("paper") or defaults.get("paper") or "a4",
        variables,
    )

    pack_strategy = _parse_pack_strategy(
        document_spec_raw.get("pack_strategy") or defaults["pack_strategy"],
        variables,
    )

    output_renderer = _parse_output_renderer(
        document_spec_raw.get("output_renderer") or defaults.get("output_renderer") or "pdf",
        variables,
    )

    return DocumentSpecification(
        name=document_name,
        paper=paper,
        pack_strategy=pack_strategy,
        output_renderer=output_renderer,
        src=document_src,
        components=document_components,
    )


def _resolve_multi_glob_variable(multi_glob, variables):
    return [resolve_variable(glob, variables) for glob in multi_glob]


def _parse_multi_component_specification(components: List[dict], variables: dict):
    return [_parse_component_specification(com, variables) for com in components]


def _parse_component_specification(component: dict, variables: dict):
    name = component.get("name") or "undefined_com"
    size = DistanceMeasure2D.parse_from(resolve_variable(component["size"], variables))
    front_images = _parse_front_images(component["front_images"], variables)
    back_images = _parse_back_images(component.get("back_images", {
        "type": "none",
    }), variables)

    return ComponentSpecification(
        name=name,
        size=size,
        front_images=front_images,
        back_images=back_images,
    )


def _parse_paper_specification(paper: Union[str, dict], variables: dict):
    if isinstance(paper, str):
        return DEFAULT_PAPER_SPECIFICATIONS[paper]

    paper_name = paper.get("name", "undefined_paper")
    paper_type = paper.get("type", "simple")
    paper_type_params = {}
    for param_name, param_value in paper.items():
        if param_name in ["name", "type"]:
            continue

        if isinstance(param_value, str):
            param_value = resolve_variable(param_value, variables)

        paper_type_params[param_name] = param_value

    return PaperSpecification(
        name=paper_name,
        type=paper_type,
        type_params=paper_type_params,
    )


def _parse_pack_strategy(strategy: Union[str, dict], variables: dict):
    if isinstance(strategy, str):
        return DEFAULT_PACK_STRATEGIES[strategy]

    name = strategy["name"]
    params = {}
    for param_name, param_value in strategy.items():
        if param_name == "name":
            continue

        if isinstance(param_value, str):
            param_value = resolve_variable(param_value, variables)

        params[param_name] = param_value

    return PackStrategySpecification(
        name=name,
        params=params,
    )


def _parse_output_renderer(renderer: Union[str, dict], variables: dict):
    if isinstance(renderer, str):
        return DEFAULT_OUTPUT_RENDERERS[renderer]

    name = renderer["name"]
    params = {}
    for param_name, param_value in renderer.items():
        if param_name == "name":
            continue

        if isinstance(param_value, str):
            param_value = resolve_variable(param_value, variables)

        params[param_name] = param_value

    return PackStrategySpecification(
        name=name,
        params=params,
    )


def _parse_front_images(raw: dict, variables: dict):
    src = MultiGlob(_resolve_multi_glob_variable(raw["src"], variables))
    mirror_vertical = raw.get("mirror_vertical", False)
    mirror_horizontal = raw.get("mirror_horizontal", False)
    return FrontImageSpecification(
        src=src,
        mirror_vertical=mirror_vertical,
        mirror_horizontal=mirror_horizontal,
    )


def _parse_back_images(raw: dict, variables: dict):
    back_type = raw.get("type", "none")

    params = {}
    for param_name, param_value in raw.items():
        if param_name == "name":
            continue

        if isinstance(param_value, str):
            param_value = resolve_variable(param_value, variables)

        params[param_name] = param_value

    return BackImageSpecification(
        type=back_type,
        type_params=params,
    )


def compile_to_yaml(spec: BGSpecification) -> str:
    pass

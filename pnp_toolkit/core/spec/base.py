from dataclasses import dataclass
from pathlib import Path
from typing import Tuple, List

from pnp_toolkit.core.measures import DistanceMeasure2D
from pnp_toolkit.core.utils import resolve_glob_pathes, path_combinations


@dataclass
class BGSpecification:
    spec_version: Tuple[int, int]
    project_name: str
    variables: dict
    output: "OutputSpecification"
    document_defaults: dict
    documents: List["DocumentSpecification"]


@dataclass
class OutputSpecification:
    directory: Path
    format: str


@dataclass
class DocumentSpecification:
    name: str

    paper: "PaperSpecification"
    pack_strategy: "PackStrategySpecification"
    output_renderer: "OutputRendererSpecification"

    src: "MultiGlob"
    components: List["ComponentSpecification"]


@dataclass
class PaperSpecification:
    name: str
    type: str
    type_params: dict


@dataclass
class PackStrategySpecification:
    name: str
    params: dict


@dataclass
class OutputRendererSpecification:
    name: str
    params: dict


@dataclass
class ComponentSpecification:
    name: str
    size: DistanceMeasure2D
    front_images: "FrontImageSpecification"
    back_images: "BackImageSpecification"


@dataclass
class FrontImageSpecification:
    src: "MultiGlob"
    mirror_vertical: bool
    mirror_horizontal: bool


@dataclass
class BackImageSpecification:
    type: str
    type_params: dict


@dataclass
class MultiGlob:
    glob_path: List[str]

    def resolve(self) -> List[Path]:
        return [Path(p) for p in resolve_glob_pathes(self.glob_path)]

    def combine(self, other: "MultiGlob") -> "MultiGlob":
        return MultiGlob(path_combinations(self.glob_path, other.glob_path))

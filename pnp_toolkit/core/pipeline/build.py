import logging
import multiprocessing
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image, ImageOps

from pnp_toolkit.core.binpack.input_types import SimplePaperSpec, Padding, Size, RollPaperSpec, PaperSpec, UnpackedItem
from pnp_toolkit.core.binpack.strategy.base import PackStrategy
from pnp_toolkit.core.binpack.strategy.simple_guillotine import SimpleGuillotinePackStrategy
from pnp_toolkit.core.measures import DistanceMeasure4D, DistanceMeasure2D, DistanceMeasure1D
from pnp_toolkit.core.render.base import OutputRenderer
from pnp_toolkit.core.render.pdf import PDFOutputRenderer
from pnp_toolkit.core.render.types import RenderDocumentFlow
from pnp_toolkit.core.spec.base import BGSpecification, DocumentSpecification, PaperSpecification, \
    PackStrategySpecification, OutputRendererSpecification, ComponentSpecification, BackImageSpecification, MultiGlob
from pnp_toolkit.core.spec.generic_parse import resolve_variable
from pnp_toolkit.core.spec.yaml_parse import _resolve_multi_glob_variable

BinPackFlow = namedtuple("BinPackFlow", ["items", "front_images", "back_images"])


class BuildPipeline:
    def __init__(self, *, max_concurrency: Optional[int] = None):
        if not max_concurrency:
            max_concurrency = multiprocessing.cpu_count()
        self._max_concurrency = max_concurrency
        self._process_status_changed_handlers = []

    def on_process_status_changed(self, handler):
        self._process_status_changed_handlers.append(handler)

    def emit_process_status_changed(self, doc: DocumentSpecification, completion: float, status: str):
        for handler in self._process_status_changed_handlers:
            handler(doc, completion, status)

    def process_all(self, spec: BGSpecification):
        self.process_specific(spec, [doc.name for doc in spec.documents])

    def process_specific(self, spec: BGSpecification, doc_names: List[str]):
        task_create_datetime = datetime.now()

        with ThreadPoolExecutor(max_workers=self._max_concurrency) as executor:
            for doc in spec.documents:
                if doc.name not in doc_names:
                    continue

                executor.submit(BuildPipeline._process_single, self, doc, spec, task_create_datetime.isoformat())
                # self._process_single(doc, spec, task_create_datetime.isoformat())

    def _process_single(self, doc: DocumentSpecification, spec: BGSpecification, task_create_datetime: str):
        self.emit_process_status_changed(doc, 0.0, "prepare document for process")

        binpack_paper = self._convert_paper_spec_to_binpack_paper(doc.paper, spec)
        binpack_strategy = self._convert_binpack_strategy(doc.pack_strategy, spec)

        if type(binpack_paper) not in binpack_strategy.supported_paper():
            raise ValueError(f"Selected strategy '{doc.pack_strategy.name}' not support paper type '{doc.paper.name}'")

        output_path = self._build_output_path(doc, spec, task_create_datetime)
        output_renderer = self._convert_output_renderer(doc.output_renderer, output_path, spec)

        self.emit_process_status_changed(doc, 1/4, "prepare components for packing")
        binpack_flow = self._convert_component_specs_to_binpack_flow(doc.components, doc, spec.variables)

        self.emit_process_status_changed(doc, 2/4, "pack components")
        packed_document = binpack_strategy.pack(binpack_paper, binpack_flow.items)

        render_flow = RenderDocumentFlow(
            packed_document=packed_document,
            front_images=binpack_flow.front_images,
            back_images=binpack_flow.back_images
        )

        self.emit_process_status_changed(doc, 3/4, "render packed document")
        output_renderer.render(render_flow)
        self.emit_process_status_changed(doc, 4/4, "complete")

    @staticmethod
    def _convert_component_specs_to_binpack_flow(component_item: List[ComponentSpecification], doc: DocumentSpecification, variables: dict) -> BinPackFlow:
        unpacked_items = []
        front_images = {}
        back_images = {}
        idx = 0

        for com in component_item:
            back_image_factory = BuildPipeline._get_back_image_factory(com.back_images, doc, variables)

            front_image_paths = doc.src.combine(com.front_images.src).resolve()
            for front_image_path in front_image_paths:
                front_image_pil = BuildPipeline._read_pillow_image(front_image_path)

                if com.front_images.mirror_vertical:
                    front_image_pil = ImageOps.flip(front_image_pil)
                if com.front_images.mirror_horizontal:
                    front_image_pil = ImageOps.mirror(front_image_pil)

                back_image_pil = back_image_factory(front_image_path)
                mm_size = com.size.to_mm()
                raw_size = Size(mm_size.x, mm_size.y)
                unpacked_item = UnpackedItem(id=idx, size=raw_size, back_exists=back_image_pil is not None)

                unpacked_items.append(unpacked_item)
                front_images[idx] = front_image_pil
                if unpacked_item.back_exists:
                    back_images[idx] = back_image_pil

                idx += 1

        return BinPackFlow(unpacked_items, front_images, back_images)

    @staticmethod
    def _get_back_image_factory(back_image: BackImageSpecification, doc: DocumentSpecification, variables: dict):
        params = back_image.type_params

        if back_image.type == "none":
            return lambda _: None

        if back_image.type == "first_image":
            back_image_src = MultiGlob(_resolve_multi_glob_variable(params["src"], variables))
            resolved_back_images = doc.src.combine(back_image_src).resolve()
            if not resolved_back_images:
                raise ValueError(f"Back image by path {back_image_src.glob_path} not found")
            first_back_image_path = resolved_back_images[0]
            first_back_image_pil = BuildPipeline._read_pillow_image(first_back_image_path)

            return lambda _: first_back_image_pil

        raise ValueError(f"Not supported back image type {back_image.type}")

    @staticmethod
    def _read_pillow_image(path: Path):
        with Image.open(path) as orig:
            return orig.copy()

    @staticmethod
    def _build_output_path(doc: DocumentSpecification, spec: BGSpecification, task_create_datetime: str):
        output_info = spec.output
        base_path = output_info.directory
        format_path = resolve_variable(output_info.format, {
            **spec.variables,
            "paper_name": doc.paper.name,
            "doc_name": doc.name,
            "doc_ext": doc.output_renderer.name,
            "file_name": f"{doc.name}.{doc.output_renderer.name}",
            "doc_create_datetime": datetime.now().isoformat(),
            "task_create_datetime": task_create_datetime,
        }, Path)
        return base_path / format_path

    @staticmethod
    def _convert_output_renderer(renderer_spec: OutputRendererSpecification, output_path: Path, spec: BGSpecification) -> OutputRenderer:
        params = renderer_spec.name
        if renderer_spec.name == "pdf":
            return PDFOutputRenderer(
                output_path=output_path,
            )

        raise ValueError(f"Unsupported output_renderer type '{renderer_spec.name}'")

    @staticmethod
    def _convert_binpack_strategy(strategy_spec: PackStrategySpecification, spec: BGSpecification) -> PackStrategy:
        params = strategy_spec.params

        if strategy_spec.name == "simple_guillotine":
            rotation = params.get("rotation", False)
            return SimpleGuillotinePackStrategy(rotation=rotation)

        raise ValueError(f"Unsupported pack_strategy type '{strategy_spec.name}'")

    @staticmethod
    def _convert_paper_spec_to_binpack_paper(paper_spec: PaperSpecification, spec: BGSpecification) -> PaperSpec:
        params = paper_spec.type_params
        if paper_spec.type == "simple":
            raw_size = resolve_variable(params["size"], spec.variables)
            size = DistanceMeasure2D.parse_from(raw_size).to_mm()

            raw_padding = resolve_variable(params.get("padding", "0*0*0*0mm"), spec.variables)
            padding = DistanceMeasure4D.parse_from(raw_padding).to_mm()

            return SimplePaperSpec(
                size=Size(size.x, size.y),
                padding=Padding(padding.x, padding.y, padding.z, padding.w),
            )

        if paper_spec.type == "roll":
            raw_size = resolve_variable(params["width"], spec.variables)
            size = DistanceMeasure1D.parse_from(raw_size).to_mm()

            raw_padding = resolve_variable(params.get("padding", "0*0*0*0mm"), spec.variables)
            padding = DistanceMeasure4D.parse_from(raw_padding).to_mm()

            return RollPaperSpec(
                width=size.x,
                padding=Padding(padding.x, padding.y, padding.z, padding.w),
            )

        raise ValueError(f"Unsupported paper type {paper_spec.type}")

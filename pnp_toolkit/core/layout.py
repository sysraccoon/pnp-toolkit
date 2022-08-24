from typing import Tuple

from pnp_toolkit.core.structs import PaperSpec, Size


def search_effective_orientation(paper: PaperSpec, image_size: Size) -> PaperSpec:
    portrait_image_count = calculate_image_count(paper, image_size)
    landscape_paper = paper.rotate()
    landscape_image_count = calculate_image_count(landscape_paper, image_size)

    if landscape_image_count > portrait_image_count:
        return landscape_paper

    return paper


def calculate_image_count(paper: PaperSpec, image_size: Size):
    nup = calculate_effective_layout(paper.work_area(), image_size)
    image_count = nup[0] * nup[1]
    return image_count


def calculate_effective_layout(work_area: Size, image_size: Size) -> Tuple[int, int]:
    horizontal_layout = int(work_area.width_mm / image_size.width_mm)
    vertical_layout = int(work_area.height_mm / image_size.height_mm)

    return horizontal_layout, vertical_layout

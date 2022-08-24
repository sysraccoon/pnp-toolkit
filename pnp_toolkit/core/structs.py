from copy import copy
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class Offset:
    top_mm: float = 0.0
    right_mm: float = 0.0
    bottom_mm: float = 0.0
    left_mm: float = 0.0


@dataclass
class Size:
    width_mm: float = 0.0
    height_mm: float = 0.0


@dataclass
class PaperSpec:
    size: Size
    margins: Offset = field(default_factory=Offset)
    special: bool = False

    def work_area(self) -> Size:
        expected_work_area = copy(self.size)
        expected_work_area.height_mm -= self.margins.top_mm + self.margins.bottom_mm
        expected_work_area.width_mm -= self.margins.left_mm + self.margins.right_mm
        return expected_work_area

    def rotate(self, rotate_times: int = 1) -> "PaperSpec":
        assert rotate_times >= 0
        rotated_paper = copy(self)

        for _ in range(rotate_times):
            rotated_paper.margins = Offset(
                rotated_paper.margins.left_mm, rotated_paper.margins.top_mm,
                rotated_paper.margins.right_mm, rotated_paper.margins.bottom_mm,
            )

            rotated_paper.size = Size(
                rotated_paper.size.height_mm,
                rotated_paper.size.width_mm,
            )

        return rotated_paper
    
    @classmethod
    def from_spec_paper(cls, paper_spec):
        return cls(paper_spec.size)


@dataclass
class LayoutSpec:
    size: Size
    mirror: bool


@dataclass
class CombinedLayout:
    paper: PaperSpec
    image_layout: LayoutSpec
    search_optimal_paper_orientation: bool = True
    # search optimal image nup if set None
    image_nup: Tuple[int, int] = None

    # cached values
    _paper_work_area: Size = None
    _image_per_page: int = None
    _layout_area: Size = None
    _image_size: Size = None

    def __post_init__(self):
        self._image_size = self.image_layout.size
        if self.search_optimal_paper_orientation:
            self.paper = self._search_effective_orientation(self.paper, self._image_size)
        self._paper_work_area = self.paper.work_area()
        if not self.image_nup:
            self.image_nup = self._calculate_effective_layout(self.paper.work_area(), self._image_size)
        self._image_per_page = self.image_nup[0] * self.image_nup[1]
        self._layout_area = Size(self._image_size.width_mm * self.image_nup[0], self._image_size.height_mm * self.image_nup[1])

    def index_to_coordinates(self, i):
        return i % self.image_nup[0], i // self.image_nup[0]

    def coordinates_to_position(self, x, y, mirror=False):
        if self.image_layout.mirror:
            mirror = not mirror

        if mirror:
            x = self.image_nup[0] - x - 1

        offset_x_for_center = (self._paper_work_area.width_mm - self._layout_area.width_mm) / 2 + self.paper.margins.left_mm
        offset_y_for_center = (self._paper_work_area.height_mm - self._layout_area.height_mm) / 2 + self.paper.margins.top_mm

        work_x = x * self._image_size.width_mm
        work_y = y * self._image_size.height_mm

        return offset_x_for_center + work_x, offset_y_for_center + work_y

    @staticmethod
    def _search_effective_orientation(paper: PaperSpec, image_size: Size) -> PaperSpec:
        portrait_image_count = CombinedLayout._calculate_image_count(paper, image_size)
        landscape_paper = paper.rotate()
        landscape_image_count = CombinedLayout._calculate_image_count(landscape_paper, image_size)

        if landscape_image_count > portrait_image_count:
            return landscape_paper

        return paper

    @staticmethod
    def _calculate_image_count(paper: PaperSpec, image_size: Size):
        nup = CombinedLayout._calculate_effective_layout(paper.work_area(), image_size)
        image_count = nup[0] * nup[1]
        return image_count

    @staticmethod
    def _calculate_effective_layout(work_area: Size, image_size: Size) -> Tuple[int, int]:
        horizontal_layout = int(work_area.width_mm / image_size.width_mm)
        vertical_layout = int(work_area.height_mm / image_size.height_mm)

        return horizontal_layout, vertical_layout

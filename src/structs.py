from dataclasses import dataclass, field
from typing import List, Tuple
from copy import copy


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


@dataclass
class ExpectedImageSpec:
    size: Size
    mirror: bool = False


@dataclass
class ImageLayout:
    paper: PaperSpec
    expected_image: ExpectedImageSpec

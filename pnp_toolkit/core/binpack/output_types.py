from dataclasses import dataclass
from typing import Union, List

from pnp_toolkit.core.binpack.input_types import Size, Position


@dataclass
class PackedItemFront:
    position: Position
    size: Size
    id: int
    rotated: bool = False


@dataclass
class PackedItemBack:
    position: Position
    size: Size
    id: int
    rotated: bool = False


PackedItem = Union[PackedItemFront, PackedItemBack]


@dataclass
class PackedPage:
    size: Size
    items: List[PackedItem]


@dataclass
class PackedDocument:
    pages: List[PackedPage]

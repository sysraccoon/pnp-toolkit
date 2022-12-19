import itertools

from pnp_toolkit.core.binpack.input_types import Position, Size
from pnp_toolkit.core.binpack.output_types import PackedDocument, PackedItemFront, PackedItemBack


def assert_packed_intersections(doc: PackedDocument):
    for page in doc.pages:
        only_fronts_and_backs = [
            i for i in page.items if isinstance(i, PackedItemFront) or isinstance(i, PackedItemBack)
        ]
        for first_item, second_item in itertools.combinations(only_fronts_and_backs, 2):
            assert not rect_intersect(
                pos1=first_item.position, size1=first_item.size,
                pos2=second_item.position, size2=second_item.size
            ), "packed item intersection"


def rect_intersect(pos1: Position, size1: Size, pos2: Position, size2: Size) -> bool:
    x = max(pos1.x, pos2.x)
    num1 = min(pos1.x + size1.width, pos2.x + size2.width)
    y = max(pos1.y, pos2.y)
    num2 = min(pos1.y + size1.height, pos2.y + size2.height)

    return num1 > x and num2 > y


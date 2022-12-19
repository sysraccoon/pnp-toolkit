import sys
from collections import namedtuple
from copy import deepcopy
from typing import List, Type

from pnp_toolkit.core.binpack.input_types import RollPaperSpec, UnpackedItem, Size, PaperSpec, Position
from pnp_toolkit.core.binpack.output_types import PackedDocument, PackedPage, PackedItem, PackedItemFront
from pnp_toolkit.core.binpack.strategy.base import PackStrategy
from pnp_toolkit.core.binpack.utils import generate_back_page


class RollGuillotinePackStrategy(PackStrategy):
    def pack(self, paper_spec: RollPaperSpec, items: List[UnpackedItem]) -> PackedDocument:

        work_width = paper_spec.width - paper_spec.padding.left - paper_spec.padding.right
        boxes = []
        box_id_to_item_id = {}

        for idx, item in enumerate(items):
            box = (item.size.width, item.size.height)
            boxes.append(box)
            box_id_to_item_id[idx] = item.id

        height, rectangles = phsppog(work_width, boxes)

        result_width = paper_spec.width
        result_height = height + paper_spec.padding.top + paper_spec.padding.bottom

        result_page_size = Size(result_width, result_height)

        packed_items = []

        for idx, rect in enumerate(rectangles):
            item_id = box_id_to_item_id[idx]
            pos_x = rect.x + paper_spec.padding.left
            pos_y = rect.y + paper_spec.padding.top
            front_item = PackedItemFront(
                id=item_id,
                position=Position(pos_x, pos_y),
                size=Size(rect.w, rect.h),
            )
            packed_items.append(front_item)

        packed_page = PackedPage(size=result_page_size, items=packed_items)
        packed_pages = [packed_page]

        items_with_backs = {i.id for i in items if i.back_exists}
        back_page = generate_back_page(packed_page, items_with_backs)
        if len(back_page.items) != 0:
            packed_pages.append(back_page)

        return PackedDocument(packed_pages)

    def supported_paper(self) -> List[Type[PaperSpec]]:
        return [RollPaperSpec]


Rectangle = namedtuple('Rectangle', ['x', 'y', 'w', 'h'])


def phspprg(width, rectangles, sorting="width"):
    """
    The PH heuristic for the Strip Packing Problem. This is the RG variant, which means that rotations by
    90 degrees are allowed and that there is a guillotine constraint.
    Parameters
    ----------
    width
        The width of the strip.
    rectangles
        List of list containing width and height of every rectangle, [[w_1, h_1], ..., [w_n,h_h]].
        It is assumed that all rectangles can fit into the strip.
    sorting : string, {'width', 'height'}, default='width'
        The heuristic uses sorting to determine which rectangles to place first.
        By default sorting happens on the width but can be changed to height.
    Returns
    -------
    height
        The height of the strip needed to pack all the items.
    rectangles : list of namedtuple('Rectangle', ['x', 'y', 'w', 'h'])
        A list of rectangles, in the same order as the input list. This contains bottom left x and y coordinate and
        the width and height (which can be flipped compared to input).
    """
    if sorting not in ["width", "height" ]:
        raise ValueError("The algorithm only supports sorting by width or height but {} was given.".format(sorting))
    if sorting == "width":
        wh = 0
    else:
        wh = 1

    result = [None] * len(rectangles)
    remaining = deepcopy(rectangles)
    for idx, r in enumerate(remaining):
        if r[0] > r[1]:
            remaining[idx][0], remaining[idx][1] = remaining[idx][1], remaining[idx][0]

    sorted_indices = sorted(range(len(remaining)), key=lambda x: -remaining[x][wh])

    sorted_rect = [remaining[idx] for idx in sorted_indices]

    x, y, w, h, H = 0, 0, 0, 0, 0
    while sorted_indices:
        idx = sorted_indices.pop(0)
        r = remaining[idx]
        if r[1] > width:
            result[idx] = Rectangle(x, y, r[0], r[1])
            x, y, w, h, H = r[0], H, width - r[0], r[1], H + r[1]
        else:
            result[idx] = Rectangle(x, y, r[1], r[0])
            x, y, w, h, H = r[1], H, width - r[1], r[0], H + r[0]
        recursive_packing(x, y, w, h, 1, remaining, sorted_indices, result)
        x, y = 0, H
    
    return H, result


def phsppog(width, rectangles, sorting="width"):
    """
    The PH heuristic for the Strip Packing Problem. This is the OG variant, which means that rotations are
    NOT allowed and that there is a guillotine contraint.
    Parameters
    ----------
    width
        The width of the strip.
    rectangles
        List of list containing width and height of every rectangle, [[w_1, h_1], ..., [w_n,h_h]].
        It is assumed that all rectangles can fit into the strip.
    sorting : string, {'width', 'height'}, default='width'
        The heuristic uses sorting to determine which rectangles to place first.
        By default sorting happens on the width but can be changed to height.
    Returns
    -------
    height
        The height of the strip needed to pack all the items.
    rectangles : list of namedtuple('Rectangle', ['x', 'y', 'w', 'h'])
        A list of rectangles, in the same order as the input list. This contains bottom left x and y coordinate and
        the width and height (which can be flipped compared to input).
    """
    if sorting not in ["width", "height" ]:
        raise ValueError("The algorithm only supports sorting by width or height but {} was given.".format(sorting))
    if sorting == "width":
        wh = 0
    else:
        wh = 1
    
    result = [None] * len(rectangles)
    remaining = deepcopy(rectangles)
    
    sorted_indices = sorted(range(len(remaining)), key=lambda x: -remaining[x][wh])
    
    sorted_rect = [remaining[idx] for idx in sorted_indices]
    
    x, y, w, h, H = 0, 0, 0, 0, 0
    while sorted_indices:
        idx = sorted_indices.pop(0)
        r = remaining[idx]
        result[idx] = Rectangle(x, y, r[0], r[1])
        x, y, w, h, H = r[0], H, width - r[0], r[1], H + r[1]
        recursive_packing(x, y, w, h, 0, remaining, sorted_indices, result)
        x, y = 0, H
    

    return H, result


def recursive_packing(x, y, w, h, D, remaining, indices, result):
    """Helper function to recursively fit a certain area."""
    priority = 6
    for idx in indices:
        for j in range(0, D + 1):
            if priority > 1 and remaining[idx][(0 + j) % 2] == w and remaining[idx][(1 + j) % 2] == h:
                priority, orientation, best = 1, j, idx
                break
            elif priority > 2 and remaining[idx][(0 + j) % 2] == w and remaining[idx][(1 + j) % 2] < h:
                priority, orientation, best = 2, j, idx
            elif priority > 3 and remaining[idx][(0 + j) % 2] < w and remaining[idx][(1 + j) % 2] == h:
                priority, orientation, best = 3, j, idx
            elif priority > 4 and remaining[idx][(0 + j) % 2] < w and remaining[idx][(1 + j) % 2] < h:
                priority, orientation, best = 4, j, idx
            elif priority > 5:
                priority, orientation, best = 5, j, idx
    if priority < 5:
        if orientation == 0:
            omega, d = remaining[best][0], remaining[best][1]
        else:
            omega, d = remaining[best][1], remaining[best][0]
        result[best] = Rectangle(x, y, omega, d)
        indices.remove(best)
        if priority == 2:
            recursive_packing(x, y + d, w, h - d, D, remaining, indices, result)
        elif priority == 3:
            recursive_packing(x + omega, y, w - omega, h, D, remaining, indices, result)
        elif priority == 4:
            min_w = sys.maxsize
            min_h = sys.maxsize
            for idx in indices:
                min_w = min(min_w, remaining[idx][0])
                min_h = min(min_h, remaining[idx][1])
            # Because we can rotate:
            min_w = min(min_h, min_w)
            min_h = min_w
            if w - omega < min_w:
                recursive_packing(x, y + d, w, h - d, D, remaining, indices, result)
            elif h - d < min_h:
                recursive_packing(x + omega, y, w - omega, h, D, remaining, indices, result)
            elif omega < min_w:
                recursive_packing(x + omega, y, w - omega, d, D, remaining, indices, result)
                recursive_packing(x, y + d, w, h - d, D, remaining, indices, result)
            else:
                recursive_packing(x, y + d, omega, h - d, D, remaining, indices, result)
                recursive_packing(x + omega, y, w - omega, h, D, remaining, indices, result)
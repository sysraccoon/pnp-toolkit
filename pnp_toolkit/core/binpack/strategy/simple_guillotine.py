from typing import List, Type

import typing

from sortedcontainers import SortedListWithKey

from pnp_toolkit.core.binpack.input_types import UnpackedItem, PaperSpec, SimplePaperSpec, Size, Position
from pnp_toolkit.core.binpack.output_types import PackedDocument, PackedItem, PackedItemFront, PackedPage
from pnp_toolkit.core.binpack.strategy.base import PackStrategy
from pnp_toolkit.core.binpack.utils import generate_back_page


class FreeRectangle(
    typing.NamedTuple('FreeRectangle', [('width', float), ('height', float), ('x', float), ('y', float)])
):
    __slots__ = ()

    @property
    def area(self):
        return self.width * self.height


class GuillotineBin:
    def __init__(self,
                 size: Size,
                 rotation: bool = True,
                 rectangle_merge: bool = True,
                 split_heuristic: str = 'default') -> None:
        self.size = size
        self.area = self.size.width * self.size.height
        self.free_area = self.size.width * self.size.height
        self.rMerge = rectangle_merge
        self.split_heuristic = split_heuristic

        self._score = self.scoreBAF

        if self.size.width == 0 or self.size.height == 0:
            # self.freerects = [] # type: List[FreeRectangle]
            self.freerects = SortedListWithKey(iterable=None, key=lambda x: x.area)
        else:
            self.freerects = SortedListWithKey([FreeRectangle(self.size.width, self.size.height, 0, 0)],
                                               key=lambda x: x.area)
        self.items = []  # type: List[PackedItem]
        self.rotation = rotation

    @staticmethod
    def scoreBAF(rect: FreeRectangle, item: UnpackedItem) -> typing.Tuple[float, float]:
        """ Best Area Fit """
        return rect.area - item.size.area, min(rect.width - item.size.width, rect.height - item.size.height)

    def __repr__(self) -> str:
        return "Guillotine(%r)" % self.items

    @staticmethod
    def _item_fits_rect(item: UnpackedItem,
                        rect: FreeRectangle,
                        rotation: bool = False) -> bool:
        if (not rotation and
                item.size.width <= rect.width and
                item.size.height <= rect.height):
            return True
        if (rotation and
                item.size.height <= rect.width and
                item.size.width <= rect.height):
            return True
        return False

    @staticmethod
    def _split_along_axis(
            free_rect: FreeRectangle,
            item: UnpackedItem,
            split: bool
    ) -> List[FreeRectangle]:
        top_x = free_rect.x
        top_y = free_rect.y + item.size.height
        top_h = free_rect.height - item.size.height

        right_x = free_rect.x + item.size.width
        right_y = free_rect.y
        right_w = free_rect.width - item.size.width

        # horizontal split
        if split:
            top_w = free_rect.width
            right_h = item.size.height
        # vertical split
        else:
            top_w = item.size.width
            right_h = free_rect.height

        result = []

        if right_w > 0 and right_h > 0:
            right_rect = FreeRectangle(right_w, right_h, right_x, right_y)
            result.append(right_rect)

        if top_w > 0 and top_h > 0:
            top_rect = FreeRectangle(top_w, top_h, top_x, top_y)
            result.append(top_rect)
        return result

    def _split_free_rect(
            self,
            item: UnpackedItem,
            free_rect: FreeRectangle
    ) -> List[FreeRectangle]:
        """
        Determines the split axis based upon the split heuristic then calls
        _split_along_axis  with the appropriate axis to return a List[FreeRectangle].
        """

        # Leftover lengths
        w = free_rect.width - item.size.width
        h = free_rect.height - item.size.height

        if self.split_heuristic == 'SplitShorterLeftoverAxis':
            split = (w <= h)
        elif self.split_heuristic == 'SplitLongerLeftoverAxis':
            split = (w > h)
        elif self.split_heuristic == 'SplitMinimizeArea':
            split = (item.size.width * h > w * item.size.height)
        elif self.split_heuristic == 'SplitMaximizeArea':
            split = (item.size.width * h <= w * item.size.height)
        elif self.split_heuristic == 'SplitShorterAxis':
            split = (free_rect.width <= free_rect.height)
        elif self.split_heuristic == 'SplitLongerAxis':
            split = (free_rect.width > free_rect.height)
        else:
            split = True

        return self._split_along_axis(free_rect, item, split)

    def _add_item(self, item: UnpackedItem, x: int, y: int, rotate: bool = False) -> None:
        """ Helper method for adding items to the bin """
        size = item.size
        if rotate:
            size = Size(size.height, size.width)

        packed_item = PackedItemFront(
            id=item.id,
            position=Position(x, y),
            size=size,
            rotated=rotate,
        )
        self.items.append(packed_item)
        self.free_area -= size.area

    def rectangle_merge(self) -> None:
        """
        Rectangle Merge optimization
        Finds pairs of free rectangles and merges them if they are mergable.
        """
        for freerect in self.freerects:
            widths_func = lambda r: (r.width == freerect.width and
                                     r.x == freerect.x and r != freerect)
            matching_widths = list(filter(widths_func, self.freerects))
            heights_func = lambda r: (r.height == freerect.height and
                                      r.y == freerect.y and r != freerect)
            matching_heights = list(filter(heights_func, self.freerects))
            if matching_widths:
                widths_adjacent = list(
                    filter(lambda r: r.y == freerect.y + freerect.height, matching_widths))  # type: List[FreeRectangle]

                if widths_adjacent:
                    match_rect = widths_adjacent[0]
                    merged_rect = FreeRectangle(freerect.width,
                                                freerect.height + match_rect.height,
                                                freerect.x,
                                                freerect.y)
                    self.freerects.remove(freerect)
                    self.freerects.remove(match_rect)
                    self.freerects.add(merged_rect)

            if matching_heights:
                heights_adjacent = list(filter(lambda r: r.x == freerect.x + freerect.width, matching_heights))
                if heights_adjacent:
                    match_rect = heights_adjacent[0]
                    merged_rect = FreeRectangle(freerect.width + match_rect.width,
                                                freerect.height,
                                                freerect.x,
                                                freerect.y)
                    self.freerects.remove(freerect)
                    self.freerects.remove(match_rect)
                    self.freerects.add(merged_rect)

    def _find_best_score(self, item: UnpackedItem):
        rects = []
        for rect in self.freerects:
            if self._item_fits_rect(item, rect):
                rects.append((self._score(rect, item), rect, False))
            if self.rotation and self._item_fits_rect(item, rect, rotation=True):
                rects.append((self._score(rect, item), rect, True))
        try:
            _score, rect, rot = min(rects, key=lambda x: x[0])
            return _score, rect, rot
        except ValueError:
            return None, None, False

    def insert(self, item: UnpackedItem) -> bool:
        """
        Add items to the bin. Public Method.
        """
        _, best_rect, rotated = self._find_best_score(item)
        if best_rect:
            self._add_item(item, best_rect.x, best_rect.y, rotated)
            self.freerects.remove(best_rect)
            splits = self._split_free_rect(item, best_rect)
            for rect in splits:
                self.freerects.add(rect)
            if self.rMerge:
                self.rectangle_merge()
            return True
        return False

    def bin_stats(self) -> dict:
        """
        Returns a dictionary with compiled stats on the bin tree
        """

        stats = {
            'width': self.size.width,
            'height': self.size.height,
            'area': self.area,
            'efficiency': (self.area - self.free_area) / self.area,
            'items': self.items,
        }

        return stats


class SimpleGuillotinePackStrategy(PackStrategy):
    def __init__(self, rotation: bool = True):
        self.rotation = rotation

    def pack(self, paper_spec: SimplePaperSpec, items: List[UnpackedItem]) -> PackedDocument:
        items = self._sort_items(items)
        work_area = Size(
            width=paper_spec.size.width - paper_spec.padding.left - paper_spec.padding.right,
            height=paper_spec.size.height - paper_spec.padding.top - paper_spec.padding.bottom,
        )

        bins = [self._bin_factory(work_area)]

        for item in items:
            # Ensure item can theoretically fit the bin
            item_fits = False
            if (item.size.width <= work_area.width and
                    item.size.height <= work_area.height):
                item_fits = True
            if (self.rotation and
                    (item.size.height <= work_area.width and
                     item.size.width <= work_area.height)):
                item_fits = True

            if not item_fits:
                raise ValueError("Error! item too big for bin")

            scores = []
            for binn in bins:
                s, _, _ = binn._find_best_score(item)[:3]
                if s is not None:
                    scores.append((s, binn))
            if scores:
                _, best_bin = min(scores, key=lambda x: x[0])
                best_bin.insert(item)
                continue

            new_bin = self._bin_factory(work_area)
            new_bin.insert(item)
            bins.append(new_bin)

        items_with_backs = {i.id for i in items if i.back_exists}

        packed_pages = []
        for binn in bins:
            packed_items = []
            for bin_item in binn.items:
                item_pos = bin_item.position
                item_pos.x += paper_spec.padding.left
                item_pos.y += paper_spec.padding.top
                packed_items.append(bin_item)

            packed_page = PackedPage(size=paper_spec.size, items=packed_items)
            packed_pages.append(packed_page)
            packed_pages.append(generate_back_page(packed_page, items_with_backs))

        return PackedDocument(pages=packed_pages)

    def _bin_factory(self, work_area: Size):
        return GuillotineBin(work_area, self.rotation)

    def _sort_items(self, components: List[UnpackedItem]) -> List[UnpackedItem]:
        key = lambda el: el.size.width * el.size.height
        components.sort(key=key, reverse=True)
        return components

    def supported_paper(self) -> List[Type[PaperSpec]]:
        return [SimplePaperSpec]

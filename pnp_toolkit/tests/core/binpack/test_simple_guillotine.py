import itertools
from typing import List

import pytest

from pnp_toolkit.core.binpack.input_types import SimplePaperSpec, Size, Padding, UnpackedItem, Position
from pnp_toolkit.core.binpack.output_types import PackedDocument, PackedItemFront, PackedItemBack
from pnp_toolkit.core.binpack.strategy.simple_guillotine import SimpleGuillotinePackStrategy
from pnp_toolkit.tests.core.binpack.utils import assert_packed_intersections


@pytest.mark.parametrize(
    "paper_spec,unpacked_items,estimate_page_count",
    [
        (
            SimplePaperSpec(size=Size(210, 297), padding=Padding(5, 5, 5, 5)),
            [
                UnpackedItem(0, Size(20, 30)),
                UnpackedItem(1, Size(30, 20)),
                UnpackedItem(2, Size(40, 40)),
                UnpackedItem(3, Size(50, 90)),
            ],
            1,
        ),
        (
                SimplePaperSpec(size=Size(210, 297), padding=Padding(5, 5, 5, 5)),
                [
                    UnpackedItem(i, Size(63, 88.5))
                    for i in range(9)
                ],
                1,
        ),
        (
                SimplePaperSpec(size=Size(210, 297), padding=Padding(5, 5, 5, 5)),
                [
                    UnpackedItem(i, Size(63, 88.5))
                    for i in range(19)
                ],
                3,
        ),
    ],
)
def test_simple_guillotine_pack(
        paper_spec: SimplePaperSpec,
        unpacked_items: List[UnpackedItem],
        estimate_page_count: int
):
    pack_strategy = SimpleGuillotinePackStrategy(rotation=False)

    packed_document = pack_strategy.pack(paper_spec, unpacked_items)
    assert len(packed_document.pages) == estimate_page_count
    assert_packed_intersections(packed_document)




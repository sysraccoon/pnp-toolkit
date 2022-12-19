import itertools
from typing import List

import pytest

from pnp_toolkit.core.binpack.input_types import SimplePaperSpec, Size, Padding, UnpackedItem, Position, RollPaperSpec
from pnp_toolkit.core.binpack.output_types import PackedDocument, PackedItemFront, PackedItemBack
from pnp_toolkit.core.binpack.strategy.roll_guillotine import RollGuillotinePackStrategy
from pnp_toolkit.core.binpack.strategy.simple_guillotine import SimpleGuillotinePackStrategy
from pnp_toolkit.tests.core.binpack.utils import assert_packed_intersections


@pytest.mark.parametrize(
    "paper_spec,unpacked_items",
    [
        (
                RollPaperSpec(width=210, padding=Padding(5, 5, 5, 5)),
                [
                    UnpackedItem(0, Size(20, 30)),
                    UnpackedItem(1, Size(30, 20)),
                    UnpackedItem(2, Size(40, 40)),
                    UnpackedItem(3, Size(50, 90)),
                ],
        ),
        (
                RollPaperSpec(width=210, padding=Padding(5, 5, 5, 5)),
                [
                    UnpackedItem(i, Size(63, 88.5))
                    for i in range(9)
                ],
        ),
        (
                RollPaperSpec(width=210, padding=Padding(5, 5, 5, 5)),
                [
                    UnpackedItem(i, Size(63, 88.5))
                    for i in range(19)
                ],
        ),
    ],
)
def test_simple_guillotine_pack(
        paper_spec: RollPaperSpec,
        unpacked_items: List[UnpackedItem],
):
    pack_strategy = RollGuillotinePackStrategy()

    packed_document = pack_strategy.pack(paper_spec, unpacked_items)
    assert len(packed_document.pages) == 1
    assert_packed_intersections(packed_document)


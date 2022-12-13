from pnp_toolkit.core.binpack.input_types import Size, Position
from pnp_toolkit.core.binpack.output_types import PackedPage, PackedItemFront, PackedItemBack


def generate_back_page(front_page: PackedPage, items_with_back: set) -> PackedPage:
    page_size = front_page.size
    packed_backs = []

    for front_item in front_page.items:
        if not isinstance(front_item, PackedItemFront):
            continue
        if front_item.id not in items_with_back:
            continue

        item_back = PackedItemBack(
            id=front_item.id,
            size=front_item.size,
            rotated=front_item.rotated,
            position=Position(
                x=page_size.width-front_item.position.x-front_item.size.width,
                y=front_item.position.y,
            )
        )

        packed_backs.append(item_back)

    return PackedPage(page_size, packed_backs)

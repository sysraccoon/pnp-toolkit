import logging
from io import BytesIO
from pathlib import Path

from PIL.Image import Image as PILImage
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as report_canvas
from reportlab.pdfgen.canvas import Canvas

from pnp_toolkit.core.binpack.input_types import Position, Size
from pnp_toolkit.core.binpack.output_types import PackedItemFront, PackedPage, PackedItemBack, PackedItem
from pnp_toolkit.core.render.base import OutputRenderer
from pnp_toolkit.core.render.types import RenderDocumentFlow


class PDFOutputRenderer(OutputRenderer):
    def __init__(self, output_path: Path):
        self.output_path = output_path

    def render(self, render_flow: RenderDocumentFlow):
        self.output_path.parent.mkdir(exist_ok=True, parents=True)

        packed_document = render_flow.packed_document

        canvas = report_canvas.Canvas(self.output_path.as_posix())

        for page in packed_document.pages:
            canvas.setPageSize((page.size.width * mm, page.size.height * mm))

            for item in page.items:
                self._draw_item(canvas, item, page, render_flow)

            canvas.showPage()

        canvas.save()

    def _draw_item(self, canvas: Canvas, item: PackedItem, page: PackedPage, render_flow: RenderDocumentFlow):
        if isinstance(item, PackedItemFront):
            item_id = item.id
            item_image = render_flow.front_images[item_id]
        elif isinstance(item, PackedItemBack):
            item_id = item.id
            item_image = render_flow.back_images[item_id]
        else:
            logging.warning(f"Unsupported packed item type! Provided {type(item)}")
            return

        self._draw_image(canvas, page.size, item.position, item.size, item_image)

    @staticmethod
    def _draw_image(canvas: Canvas, page_size: Size, position: Position, size: Size, image: PILImage):
        image_buffer = BytesIO()
        image.save(image_buffer, "PNG")
        image_buffer.seek(0)

        canvas.drawImage(
            ImageReader(image_buffer),
            position.x*mm,
            (page_size.height - position.y - size.height)*mm,  # fix coordinate system
            size.width*mm,
            size.height*mm,
            mask="auto",
        )

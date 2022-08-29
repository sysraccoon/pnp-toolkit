import logging
from typing import Tuple

from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as report_canvas

from pnp_toolkit.core.structs import CombinedLayout, Size


def generate_pdf(
    pdf_path,
    images_with_copy_count,
    combined_layout,
    background_pattern=None,
    signature=None,
):
    try:
        paper_spec = combined_layout.paper
        image_layout = combined_layout.image_layout
        canvas_size = (paper_spec.size.width_mm * mm, paper_spec.size.height_mm * mm)

        canvas = report_canvas.Canvas(pdf_path, pagesize=canvas_size)
        placed_images_to_page = 0
        page_number = 1
        for image, count in images_with_copy_count.items():
            for _ in range(count):
                if placed_images_to_page >= combined_layout._image_per_page:
                    draw_crosses(canvas, combined_layout)
                    if signature:
                        place_label(
                            canvas, combined_layout, f"{signature} | #{page_number}"
                        )
                    canvas.showPage()
                    if background_pattern:
                        generate_background_page(
                            canvas,
                            combined_layout,
                            background_pattern,
                            placed_images_to_page,
                        )
                    placed_images_to_page = 0
                    page_number += 1
                place_image_by_index(
                    canvas, image, combined_layout, placed_images_to_page
                )
                placed_images_to_page += 1

        if placed_images_to_page:
            draw_crosses(canvas, combined_layout)
            if signature:
                place_label(canvas, combined_layout, f"{signature} | #{page_number}")
            canvas.showPage()
            if background_pattern:
                generate_background_page(
                    canvas, combined_layout, background_pattern, placed_images_to_page
                )

        canvas.save()
    except Exception as e:
        logging.error(f"failed to generate pdf with path: '{pdf_path}'. Caused by {e}")


def place_label(canvas, combined_layout, label):
    canvas.setFont("Helvetica", 8)
    cor_x, cor_y = combined_layout.image_nup
    pos_x, pos_y = combined_layout.coordinates_to_position(
        cor_x, cor_y, combined_layout.image_layout.mirror
    )
    LABEL_OFFSET_MM = 5
    pos_y += LABEL_OFFSET_MM

    pos_x, pos_y = pos_x * mm, pos_y * mm

    canvas.drawRightString(pos_x, pos_y, label)


def generate_background_page(
    canvas, combined_layout, background_pattern, background_count
):
    ADDITIONAL_BACKGROUND_BORDER_WIDTH = 3
    for index in range(background_count):
        if combined_layout.image_layout.background_border:
            left_offset, top_offset = index_to_mm_coordinates(
                combined_layout, index, True
            )
            image_size = combined_layout._image_size
            top_offset -= ADDITIONAL_BACKGROUND_BORDER_WIDTH
            left_offset -= ADDITIONAL_BACKGROUND_BORDER_WIDTH
            width = image_size.width_mm + ADDITIONAL_BACKGROUND_BORDER_WIDTH * 2
            height = image_size.height_mm + ADDITIONAL_BACKGROUND_BORDER_WIDTH * 2
            canvas.rect(
                left_offset * mm,
                top_offset * mm,
                width=width * mm,
                height=height * mm,
                fill=1,
            )

    for index in range(background_count):
        place_image_by_index(
            canvas, background_pattern, combined_layout, index, mirror=True
        )
    canvas.showPage()


def draw_crosses(canvas: report_canvas.Canvas, combined_layout: CombinedLayout):
    cols, rows = combined_layout.image_nup
    for col in range(cols + 1):
        for row in range(rows + 1):
            coordinate = xy_to_mm_coordinates(combined_layout, col - 1, row - 1)
            x, y = coordinate
            _draw_cross(canvas, x, y)


def place_image_by_index(canvas, image, combined_layout, index, mirror=False):
    x, y = index_to_mm_coordinates(combined_layout, index, mirror)
    _draw_image(canvas, image, x, y, combined_layout.image_layout.size)


def xy_to_mm_coordinates(combined_layout, x, y, mirror=False):
    img_x, img_y = combined_layout.coordinates_to_position(x, y, mirror)
    left_offset, top_offset = _get_left_top_offset(combined_layout, img_x, img_y)
    return left_offset, top_offset


def index_to_mm_coordinates(combined_layout, index, mirror=False):
    x, y = combined_layout.index_to_coordinates(index)
    return xy_to_mm_coordinates(combined_layout, x, y, mirror)


def _get_left_top_offset(combined_layout, x, y) -> Tuple[float, float]:
    left_offset = x
    top_offset = (
        combined_layout.paper.size.height_mm - y - combined_layout._image_size.height_mm
    )

    return (left_offset, top_offset)


def _draw_cross(canvas, left, top, length=2, line_width=0.25):
    left *= mm
    top *= mm
    length *= mm
    line_width *= mm

    canvas.setStrokeColorRGB(0.9, 0.1, 0.1)
    canvas.setLineWidth(line_width)
    canvas.line(left - length, top, left + length, top)
    canvas.line(left, top - length, left, top + length)


def _draw_image(canvas, image, left, top, image_size: Size):
    canvas.drawImage(
        image,
        left * mm,
        top * mm,
        width=image_size.width_mm * mm,
        height=image_size.height_mm * mm,
        mask="auto",
    )

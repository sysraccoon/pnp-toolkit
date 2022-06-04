import subprocess
import itertools
from typing import List, Tuple
from structs import ImageLayout, Size, PaperSpec
from utils import chunks, temp_dir
from dataclasses import dataclass
from multiprocessing import Pool, cpu_count

import os
FILLER_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "filler.png")


def generate_pdf_by_layout(
    layout: ImageLayout, 
    src_images: List[str], 
    out_path: str, 
    background_src: str = None,
    mirror_layout: bool = False):
    with temp_dir() as chunk_dir:
        expected_image_size = layout.expected_image.size
        work_paper = _search_effective_orientation(layout.paper, expected_image_size)
        layout_params = _pdfjam_params(work_paper, expected_image_size)

        effective_width, effective_height = _calculate_effective_layout(work_paper.work_area(), expected_image_size)
        expected_images_per_page = effective_width * effective_height

        background_pdf = None

        pdf_files = []
        for chunk_id, img_chunk in enumerate(chunks(src_images, expected_images_per_page)):
            if background_src:
                dest_temp_pdf = f"{chunk_dir}/back_{chunk_id}.pdf"
                background_images = mirror_chunk([background_src]*len(img_chunk), effective_width)
                _generate_single_page_pdf(layout_params, background_images, dest_temp_pdf)
                background_pdf = dest_temp_pdf

            dest_temp_pdf = f"{chunk_dir}/{chunk_id}.pdf"

            if mirror_layout:
                img_chunk = mirror_chunk(img_chunk, effective_width)

            _generate_single_page_pdf(layout_params, img_chunk, dest_temp_pdf)

            pdf_files.append(dest_temp_pdf)
            if background_pdf:
                pdf_files.append(background_pdf)
                
        merge_pdf_files(pdf_files, out_path, work_paper)


def _generate_single_page_pdf(layout_params: List[str], src_images: List[str], out_file: str):
    params = [
        "pdfjam", 
        *layout_params,
        "--frame", "true", 
        "--outfile", out_file,
        "--",
        *src_images,
    ]

    subprocess.run(params, text=True, check=True, capture_output=False)

def merge_pdf_files(src_images: List[str], out_path: str, paper: PaperSpec):
    paper_size = paper.size
    params = [
        "pdfjam",
        "--papersize", f"{{{paper_size.width_mm}mm,{paper_size.height_mm}mm}}",
        "--outfile", out_path,
        "--",
        *src_images,
    ]
    subprocess.run(params, text=True, check=True, capture_output=True)


def _pdfjam_params(paper: PaperSpec, image_size: Size) -> List[str]:
    paper_size = paper.size
    work_area = paper.work_area()

    nup_x, nup_y = _calculate_effective_layout(work_area, image_size)

    total_images_size = Size(
        nup_x*image_size.width_mm,
        nup_y*image_size.height_mm,
    )

    scale = total_images_size.width_mm / paper.size.width_mm

    params = [
        "--nup", f"{nup_x}x{nup_y}",
        "--papersize", f"{{{paper_size.width_mm}mm,{paper_size.height_mm}mm}}",
        "--templatesize", f"{{{image_size.width_mm}mm}}{{{image_size.height_mm}mm}}",
        "--scale", str(scale),
    ]

    return params


def _search_effective_orientation(paper: PaperSpec, image_size: Size) -> PaperSpec:
    portrait_image_count = _calculate_image_count(paper, image_size)
    landscape_paper = paper.rotate()
    landscape_image_count = _calculate_image_count(landscape_paper, image_size)

    if landscape_image_count > portrait_image_count:
        return landscape_paper

    return paper


def _calculate_image_count(paper: PaperSpec, image_size: Size):
    nup = _calculate_effective_layout(paper.work_area(), image_size)
    image_count = nup[0] * nup[1]
    return image_count



def _calculate_effective_layout(work_area: Size, image_size: Size) -> Tuple[int, int]:
    horizontal_layout = int(work_area.width_mm / image_size.width_mm)
    vertical_layout = int(work_area.height_mm / image_size.height_mm)

    return horizontal_layout, vertical_layout


def mirror_chunk(chunk, width):
    mirrored_lines = [list(reversed(image_line)) for image_line in chunks(chunk, width)]
    last_line = mirrored_lines[-1]
    last_len = len(last_line)
    if last_len < width:
        last_line_compensation = [FILLER_IMAGE_PATH]*(width-last_len) + last_line
        mirrored_lines[-1] = last_line_compensation
    mirrored = list(itertools.chain(*mirrored_lines))
    return mirrored

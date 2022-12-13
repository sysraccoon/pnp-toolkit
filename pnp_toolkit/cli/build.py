import logging
import pprint
from multiprocessing import Pool
from pathlib import Path
from typing import List

import click
from tqdm import tqdm

from pnp_toolkit.core.pdf_generator import generate_pdf
from pnp_toolkit.core.pipeline.build import BuildPipeline
from pnp_toolkit.core.spec.yaml_parse import parse_from_yaml

from pnp_toolkit.core.structs import CombinedLayout
from pnp_toolkit.core.utils import (
    mkdir,
    join_pathes,
    path_combinations,
    resolve_glob_pathes,
    search_multiple_copies,
)
# from pnp_toolkit.core.spec import PDFBuildSpecification
import os


@click.command()
@click.option("--spec-file", type=click.Path(exists=True, dir_okay=False, file_okay=True), default="BGSpec.yml")
@click.argument("document_names", nargs=-1)
def build(document_names: List[str], *, spec_file: str):
    logging.basicConfig(level=logging.INFO)

    spec_file = Path(spec_file)
    spec_content = spec_file.read_text()
    spec_parsed = parse_from_yaml(spec_content)

    build_pipeline = BuildPipeline()

    progress_bars = {}
    try:
        def status_changed_handler(doc, completion, status):
            bar = progress_bars.get(id(doc)) or tqdm(
                total=100,
                bar_format="{postfix[0]:<10} {desc} {percentage:3.0f}%|{bar}|",
                postfix=[doc.name],
                ascii=True,
            )

            bar.update(round(completion * 100) - bar.n)
            bar.set_description_str(status)
            progress_bars[id(doc)] = bar

        build_pipeline.on_process_status_changed(status_changed_handler)

        if not document_names:
            build_pipeline.process_all(spec_parsed)
        else:
            build_pipeline.process_specific(spec_parsed, document_names)
    finally:
        for bar in progress_bars.values():
            bar.close()
        progress_bars.clear()




    # paper_specs = spec.paper_specs
    # paper_used = spec.paper_used
    # src_groups = spec.src_groups
    # layout_specs = spec.layout_specs
    #
    # pool = Pool(spec.options.parallel)
    #
    # mkdir(out_dir)
    # for paper_name in paper_used:
    #     paper_spec = paper_specs[paper_name]
    #     paper_dir = join_pathes(out_dir, paper_name)
    #     mkdir(paper_dir)
    #
    #     for group_name, group_pathes in src_groups.items():
    #         group_src_dir = list(path_combinations([src_dir], group_pathes))
    #         group_out_dir = join_pathes(paper_dir, group_name)
    #
    #         for layout_name, layout_spec in layout_specs.items():
    #             if (
    #                 paper_spec.special
    #                 and paper_name not in layout_spec.special_paper_used
    #             ):
    #                 # special paper, but layout not support it
    #                 continue
    #
    #             if not paper_spec.special and layout_spec.special_paper_used:
    #                 # special layout, but not special paper
    #                 continue
    #
    #             pdf_path = join_pathes(group_out_dir, layout_spec.file_name)
    #             layout_src = list(
    #                 path_combinations(group_src_dir, layout_spec.src_pathes)
    #             )
    #             resolved_image_pathes = resolve_glob_pathes(layout_src)
    #
    #             background_pattern = None
    #             if layout_spec.background_pattern:
    #                 background_pathes = list(
    #                     path_combinations(
    #                         group_src_dir, [layout_spec.background_pattern]
    #                     )
    #                 )
    #                 background_resolved_pathes = resolve_glob_pathes(background_pathes)
    #                 if background_resolved_pathes:
    #                     background_pattern = background_resolved_pathes[0]
    #
    #             resolved_image_pathes.sort()
    #             resolved_with_copy_count = search_multiple_copies(
    #                 resolved_image_pathes, layout_spec.multiple_copies
    #             )
    #
    #             if not len(resolved_with_copy_count):
    #                 continue
    #
    #             mkdir(group_out_dir)
    #
    #             combined_layout = CombinedLayout(paper_spec, layout_spec)
    #             pool.apply_async(
    #                 generate_pdf,
    #                 (
    #                     pdf_path,
    #                     resolved_with_copy_count,
    #                     combined_layout,
    #                     background_pattern,
    #                     f"{paper_name} | {group_name} | {layout_name}",
    #                 ),
    #             )
    #
    # pool.close()
    # pool.join()

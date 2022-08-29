from multiprocessing import Pool

from pnp_toolkit.core.pdf_generator import generate_pdf

from pnp_toolkit.core.structs import CombinedLayout
from pnp_toolkit.core.utils import (
    mkdir,
    join_pathes,
    path_combinations,
    resolve_glob_pathes,
    search_multiple_copies,
)
from pnp_toolkit.core.spec import PDFBuildSpecification
import os


def build_pdf(src_dir: str, out_dir: str, spec: PDFBuildSpecification):
    src_dir = os.path.abspath(src_dir)
    out_dir = os.path.abspath(out_dir)

    paper_specs = spec.paper_specs
    paper_used = spec.paper_used
    src_groups = spec.src_groups
    layout_specs = spec.layout_specs

    pool = Pool(spec.options.parallel)

    mkdir(out_dir)
    for paper_name in paper_used:
        paper_spec = paper_specs[paper_name]
        paper_dir = join_pathes(out_dir, paper_name)
        mkdir(paper_dir)

        for group_name, group_pathes in src_groups.items():
            group_src_dir = list(path_combinations([src_dir], group_pathes))
            group_out_dir = join_pathes(paper_dir, group_name)

            for layout_name, layout_spec in layout_specs.items():
                if (
                    paper_spec.special
                    and paper_name not in layout_spec.special_paper_used
                ):
                    # special paper, but layout not support it
                    continue

                if not paper_spec.special and layout_spec.special_paper_used:
                    # special layout, but not special paper
                    continue

                pdf_path = join_pathes(group_out_dir, layout_spec.file_name)
                layout_src = list(
                    path_combinations(group_src_dir, layout_spec.src_pathes)
                )
                resolved_image_pathes = resolve_glob_pathes(layout_src)

                background_pattern = None
                if layout_spec.background_pattern:
                    background_pathes = list(
                        path_combinations(
                            group_src_dir, [layout_spec.background_pattern]
                        )
                    )
                    background_resolved_pathes = resolve_glob_pathes(background_pathes)
                    if background_resolved_pathes:
                        background_pattern = background_resolved_pathes[0]

                resolved_image_pathes.sort()
                resolved_with_copy_count = search_multiple_copies(
                    resolved_image_pathes, layout_spec.multiple_copies
                )

                if not len(resolved_with_copy_count):
                    continue

                mkdir(group_out_dir)

                combined_layout = CombinedLayout(paper_spec, layout_spec)
                pool.apply_async(
                    generate_pdf,
                    (
                        pdf_path,
                        resolved_with_copy_count,
                        combined_layout,
                        background_pattern,
                        f"{paper_name} | {group_name} | {layout_name}",
                    ),
                )

    pool.close()
    pool.join()

import logging
from pathlib import Path
from typing import List

import click
from tqdm import tqdm

from pnp_toolkit.core.pipeline.build import BuildPipeline
from pnp_toolkit.core.spec.yaml_parse import parse_from_yaml


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

import argparse


def parse_arguments(args=None):
    parser = argparse.ArgumentParser()

    action_subparser = parser.add_subparsers(dest="action")
    build_pdf_parser = action_subparser.add_parser(
        "build-pdf", help="build pdfs from multiple images and specification"
    )

    spec_source_group = build_pdf_parser.add_mutually_exclusive_group()
    spec_source_group.add_argument("--built-in-spec", type=str)
    spec_source_group.add_argument("--custom-spec", type=str)

    build_pdf_parser.add_argument("src_dir", type=str, default=".", nargs="?")
    build_pdf_parser.add_argument(
        "out_dir", type=str, default="build_pdf_out", nargs="?"
    )

    return parser.parse_args(args)

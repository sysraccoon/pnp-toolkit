import logging
from pnp_toolkit.cli.args import parse_arguments
from pnp_toolkit.cli.build_pdf import build_pdf
from pnp_toolkit.core.spec import load_custom_spec, load_built_in_spec


def main():
    logging.basicConfig(level=logging.INFO)

    args = parse_arguments()

    if args.action != "build-pdf":
        logging.error("action expected")
        exit(1)

    if args.custom_spec:
        spec = load_custom_spec(args.custom_spec)
    elif args.built_in_spec:
        spec = load_built_in_spec(args.built_in_spec)
    else:
        logging.error("undefined specification parameters")
        exit(1)

    src_dir = args.src_dir
    out_dir = args.out_dir

    build_pdf(src_dir, out_dir, spec)


if __name__ == "__main__":
    main()

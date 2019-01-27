from .put import apply_args as apply_args_put


def apply_args(parser):
    subparsers = parser.add_subparsers()

    parser_put = subparsers.add_parser('put')

    apply_args_put(parser_put)

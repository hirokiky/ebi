import subprocess
import sys

from .ebcli import get_filename_without_extension
from .utils import TemporaryMergedYaml


default_delimiter = '__'


def main(parsed):
    if parsed.name:
        name = parsed.name
    else:
        name = default_delimiter.join([
            get_filename_without_extension(cfg_file)
            for cfg_file in parsed.cfg_files
        ])

    payload = ['eb', 'config', 'put', name,
               '--timeout=45']
    if parsed.profile:
        payload.append('--profile=' + parsed.profile)
    if parsed.region:
        payload.append('--region=' + parsed.region)

    if len(parsed.cfg_files) == 1 and not parsed.name:
        sys.exit(subprocess.call(payload))
    else:
        with TemporaryMergedYaml(parsed.cfg_files, name):
            sys.exit(subprocess.call(payload))


def apply_args(parser):
    parser.add_argument('cfg_files', nargs='+', help='(List of) configuration template name')
    parser.add_argument('--name', help='Name of saved configuration in Amazon S3')
    parser.add_argument('--profile', help='AWS account')
    parser.add_argument('--region', help='AWS region')
    parser.set_defaults(func=main)

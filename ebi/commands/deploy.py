import logging
import sys

from . import utils

logger = logging.getLogger(__name__)


def main(parsed):
    version = utils.build_application_version(parsed)
    logger.info('Ok, now deploying the version %s for %s', version, parsed.env_name)
    extra_args = ['--staged'] if parsed.staged else None
    sys.exit(utils.deploy_version(parsed.env_name, version, parsed, extra_args))


def apply_args(parser):
    parser.add_argument('app_name', help='Application name to deploy')
    parser.add_argument('env_name', help='Environ name to deploy')
    utils.add_common_args(parser)
    parser.add_argument('--staged', action='store_true', default=False,
                        help='deploy files staged in git rather than the HEAD commit')
    parser.set_defaults(func=main)

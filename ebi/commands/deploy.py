import logging
import subprocess
import sys

from .. import appversion
from . import utils

logger = logging.getLogger(__name__)


def main(parsed):
    version, description = utils.get_version_and_description(parsed)

    appversion.make_application_version(parsed.app_name, version, parsed.dockerrun, parsed.docker_compose, parsed.ebext, description)
    logger.info('Ok, now deploying the version %s for %s', version, parsed.env_name)
    payload = ['eb', 'deploy', parsed.env_name,
               f'--version={version}']
    utils.append_common_options(payload, parsed)
    if parsed.staged:
        payload.append('--staged')
    sys.exit(subprocess.call(payload))


def apply_args(parser):
    parser.add_argument('app_name', help='Application name to deploy')
    parser.add_argument('env_name', help='Environ name to deploy')
    utils.add_common_args(parser)
    parser.add_argument('--staged', action='store_true', default=False,
                        help='deploy files staged in git rather than the HEAD commit')
    parser.set_defaults(func=main)

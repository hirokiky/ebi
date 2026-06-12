import logging
import subprocess
import sys

from .. import appversion
from . import utils

logger = logging.getLogger(__name__)


def main(parsed):
    version, description = utils.get_version_and_description(parsed)

    appversion.make_application_version(parsed.app_name, version, parsed.dockerrun, parsed.docker_compose, parsed.ebext, parsed.use_ebignore, description)

    logger.info('Ok, now creating version %s for environment %s', version, parsed.env_name)
    payload = ['eb', 'create', parsed.env_name,
               '--timeout=45',
               f'--version={version}',
               f'--cname={parsed.cname}']
    utils.append_common_options(payload, parsed)
    if parsed.cfg:
        payload.append(f'--cfg={parsed.cfg}')
    sys.exit(subprocess.call(payload))


def apply_args(parser):
    parser.add_argument('app_name', help='Application name to create')
    parser.add_argument('env_name', help='Environ name to deploy')
    parser.add_argument('cname', help='cname for created server')
    utils.add_common_args(parser)
    parser.add_argument('--cfg', help='Configuration template name to eb create')
    parser.set_defaults(func=main)

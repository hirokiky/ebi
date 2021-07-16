import logging
import subprocess
import sys
import time

from .. import appversion

logger = logging.getLogger(__name__)


def main(parsed):
    if parsed.version:
        version = parsed.version
    elif parsed.prefix:
        version = "{}_{}".format(parsed.prefix, int(time.time()))
    else:
        version = str(int(time.time()))

    if parsed.description:
        description = parsed.description
    else:
        description = ''

    appversion.make_application_version(parsed.app_name, version, parsed.dockerrun, parsed.docker_compose, parsed.ebext, parsed.use_ebignore, description)
    logger.info('Ok, now deploying the version %s for %s', version, parsed.env_name)
    payload = ['eb', 'deploy', parsed.env_name,
               '--version=' + version]
    if parsed.profile:
        payload.append('--profile=' + parsed.profile)
    if parsed.region:
        payload.append('--region=' + parsed.region)
    if parsed.timeout:
        payload.append('--timeout=' + parsed.timeout)
    if parsed.staged:
        payload.append('--staged')
    sys.exit(subprocess.call(payload))


def apply_args(parser):
    parser.add_argument('app_name', help='Application name to deploy')
    parser.add_argument('env_name', help='Environ name to deploy')
    parser.add_argument('--version', help='Version label you want to specify')
    parser.add_argument('--prefix', help='Version label prefix you want to specify')
    parser.add_argument('--description', help='Description for this version')
    parser.add_argument('--profile', help='AWS account')
    parser.add_argument('--region', help='AWS region')
    parser.add_argument('--timeout', help='The number of minutes before the deploy timeout')
    parser.add_argument('--dockerrun', help='Path to file used as Dockerrun.aws.json')
    parser.add_argument('--docker-compose', help='Path to file used as docker-compose.yml')
    parser.add_argument('--ebext', help='Path to directory used as .ebextensions/')
    parser.add_argument('--use-ebignore', help='Zip project based on .ebignore',
                        action='store_true', default=True)
    parser.add_argument('--staged', action='store_true', default=False,
                        help='deploy files staged in git rather than the HEAD commit')
    parser.set_defaults(func=main)

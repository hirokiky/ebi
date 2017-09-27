import logging
import os
import subprocess
import sys
import time

from .. import appversion
from ..utils import merge_configs

logger = logging.getLogger(__name__)


def main(parsed):
    if parsed.version:
        version = parsed.version
    else:
        version = str(int(time.time()))

    appversion.make_application_version(parsed.app_name, version, parsed.dockerrun, parsed.ebext)

    logger.info('Ok, now creating version %s for environment %s', version, parsed.env_name)
    payload = ['eb', 'create', parsed.env_name,
               '--timeout=45',
               '--version=' + version,
               '--cname=' + parsed.cname]
    if parsed.profile:
        payload.append('--profile=' + parsed.profile)

    if parsed.cfg:
        if len(parsed.cfg) == 1:
            payload.append('--cfg=' + parsed.cfg[0])
        else:
            temp_cfg_location, temp_cfg_name = merge_configs(parsed.cfg)
            logger.info('Set multiple cfgs, merged as: %s', temp_cfg_location)
            payload.append('--cfg=' + temp_cfg_name)
    if parsed.region:
        payload.append('--region=' + parsed.region)
    try:
        sys.exit(subprocess.call(payload))
    finally:
        if len(parsed.cfg) > 1 and os.path.exists(temp_cfg_location):
            os.remove(temp_cfg_location)
            logger.info('removed local temporary cfg: %s', temp_cfg_location)


def apply_args(parser):
    parser.add_argument('app_name', help='Application name to create')
    parser.add_argument('env_name', help='Environ name to deploy')
    parser.add_argument('cname', help='cname for created server')
    parser.add_argument('--version', help='Version label you want to specify')
    parser.add_argument('--profile', help='AWS account')
    parser.add_argument('--region', help='AWS region')
    parser.add_argument('--dockerrun', help='Path to file used as Dockerrun.aws.json')
    parser.add_argument('--ebext', help='Path to directory used as .ebextensions/')
    parser.add_argument('--cfg', nargs='*', help='Configuration template names to eb create')
    parser.set_defaults(func=main)

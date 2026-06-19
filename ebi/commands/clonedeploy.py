import logging
import subprocess
import sys
import time

import boto3

from .. import appversion
from . import utils

logger = logging.getLogger(__name__)


def base36encode(num):
    result = ""
    base = 36
    nchar = '0123456789abcdefghijklmnopqrstuvwxyz'
    n = int(num)
    while n > 0:
        result = nchar[n % base] + result
        n //= base
    return result


def make_next_env_names(base_env_name, base_cname):
    suffix = f'-{base36encode(int(time.time()))}'
    return f'{base_env_name}{suffix}', f'{base_cname}{suffix}'


def main(parsed):
    master_env_name = utils.get_environ_name_for_cname(parsed.app_name, parsed.cname)
    next_env_name, next_env_cname = make_next_env_names(parsed.env_name, parsed.cname)

    ###
    # Cloning
    ###
    payload = ['eb', 'clone', master_env_name,
               '--timeout=45',  # Basically, it takes a while.
               f'--clone_name={next_env_name}',
               f'--cname={next_env_cname}']
    utils.append_common_options(payload, parsed)
    if parsed.exact:
        payload.append('--exact')

    r = subprocess.call(payload)
    if r != 0:
        logger.error("Failed to clone %s to environment %s",
                     master_env_name, next_env_cname)
        sys.exit(r)

    ###
    # Deploying
    ###
    version, description = utils.get_version_and_description(parsed)

    appversion.make_application_version(parsed.app_name, version, parsed.dockerrun, parsed.docker_compose, parsed.ebext, description)
    logger.info('Ok, now deploying the version %s for %s', version, next_env_name)
    utils.deploy_version(next_env_name, version, parsed)

    ###
    # Swapping
    ###

    if parsed.noswap:
        logger.info('DONE successfully without Swapping. just deployed new version environment %s',
                    next_env_name)
        return

    eb = boto3.client('elasticbeanstalk')
    logger.info('Swapping primary %s => new primary %s',
                master_env_name, next_env_name)
    eb.swap_environment_cnames(SourceEnvironmentName=master_env_name,
                               DestinationEnvironmentName=next_env_name)
    logger.info('DONE successfully. Primary %s => new primary %s.'
                'If problem, re-swap new primary to primary',
                master_env_name, next_env_name)


def apply_args(parser):
    parser.add_argument('app_name', help='Application name to deploy')
    parser.add_argument('env_name', help='Environment name')
    parser.add_argument('cname', help='cname prefix')
    parser.add_argument('--noswap', help='Without swapping, it will just deploy for secondary'
                                         'environment',
                        action='store_true', default=False)
    utils.add_common_args(parser)
    parser.add_argument('--exact', help='Prevents Elastic Beanstalk from updating'
                                        'the solution stack version',
                        action='store_true', default=False)
    parser.set_defaults(func=main)

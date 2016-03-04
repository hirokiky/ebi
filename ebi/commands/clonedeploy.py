import logging
import subprocess
import sys
import time

import boto3

from .. import appversion

logger = logging.getLogger(__name__)


def get_environ_name_for_cname(app_name, cname):
    """ Determine environment name having :param cname: on :param app_name:.

    If cname duplicated, longer one will be returned.
    For example, there are myenv.ap-northeast-1.elasticbeanstalk.com and myenv.elasticbeanstal.com,
    myenv.ap-northeast-1.elasticbeanstal.com will be returned.
    """
    eb = boto3.client('elasticbeanstalk')
    res = eb.describe_environments(ApplicationName=app_name)

    if res['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise ValueError('ElasticBeanstalk client did not return 200 for describing environments')

    for e in reversed(sorted(res['Environments'], key=lambda x: len(x['CNAME']))):
        if e['CNAME'].startswith(cname + '.'):
            return e['EnvironmentName']
    raise ValueError('Could not find environment for applied app_name and cname')


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
    suffix = '-' + str(base36encode(int(time.time())))
    return base_env_name + suffix, base_cname + suffix


def main(parsed):
    master_env_name = get_environ_name_for_cname(parsed.app_name, parsed.cname)
    next_env_name, next_env_cname = make_next_env_names(parsed.env_name, parsed.cname)

    ###
    # Cloning
    ###
    payload = ['eb', 'clone', master_env_name,
               '--exact',
               '--timeout=45',  # Basically, it takes a while.
               '--clone_name=' + next_env_name,
               '--cname=' + next_env_cname]
    if parsed.profile:
        payload.append('--profile=' + parsed.profile)
    if parsed.region:
        payload.append('--region=' + parsed.region)

    r = subprocess.call(payload)
    if r != 0:
        logger.error("Failed to clone %s to environment %s",
                     master_env_name, next_env_cname)
        sys.exit(r)

    ###
    # Deploying
    ###
    if parsed.version:
        version = parsed.version
    else:
        version = str(int(time.time()))

    appversion.make_application_version(parsed.app_name, version, parsed.dockerrun, parsed.ebext)
    logger.info('Ok, now deploying the version %s for %s', version, next_env_name)
    payload = ['eb', 'deploy', next_env_name,
               '--version=' + version]
    if parsed.profile:
        payload.append('--profile=' + parsed.profile)
    if parsed.region:
        payload.append('--region=' + parsed.region)
    r = subprocess.call(payload)
    if r != 0:
        logger.error("Failed to deploy version %s to environment %s",
                     version, next_env_name)
        sys.exit(r)

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
    parser.add_argument('--version', help='Version label you want to specify')
    parser.add_argument('--profile', help='AWS account')
    parser.add_argument('--region', help='AWS region')
    parser.add_argument('--dockerrun', help='Path to file used as Dockerrun.aws.json')
    parser.add_argument('--ebext', help='Path to directory used as .ebextensions/')
    parser.set_defaults(func=main)
